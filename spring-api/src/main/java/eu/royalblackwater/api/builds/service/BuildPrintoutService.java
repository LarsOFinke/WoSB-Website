package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.mapper.BuildDtoMapper;
import eu.royalblackwater.api.builds.repository.BuildDataRepository;
import eu.royalblackwater.api.builds.repository.queries.BuildPrintoutQueries;
import eu.royalblackwater.api.config.StorageProperties;
import eu.royalblackwater.api.dto.BuildPrintoutRead;
import eu.royalblackwater.api.files.service.ImageAssetOptimizer;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.shared.dto.BinaryDownloadDto;
import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.CacheControl;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class BuildPrintoutService {
    private static final Logger LOG = LoggerFactory.getLogger(BuildPrintoutService.class);
    private static final Pattern CACHE_KEY = Pattern.compile("[A-Za-z0-9._:-]{1,128}");
    private static final Pattern CACHE_FILE = Pattern.compile("build-(\\d+)(?:-([a-f0-9]{64}))?\\.png");
    private static final Duration TEMPORARY_MAX_AGE = Duration.ofHours(1);
    private static final Duration ORPHAN_GRACE = Duration.ofHours(1);
    private static final Duration CLIENT_CACHE_MAX_AGE = Duration.ofDays(30);
    private final BuildDataRepository repository;
    private final StorageProperties storage;
    private final ImageAssetOptimizer imageOptimizer;
    private final AuditService audit;
    private final Clock clock;

    BuildPrintoutService(BuildDataRepository repository, StorageProperties storage,
                         ImageAssetOptimizer imageOptimizer, AuditService audit, Clock clock) {
        this.repository = repository; this.storage = storage; this.imageOptimizer = imageOptimizer;
        this.audit = audit; this.clock = clock;
    }

    @Transactional
    public BuildPrintoutRead save(long buildId, MultipartFile upload, String cacheKey,
            LocalDateTime sourceUpdatedAt, AuthenticatedUser actor) {
        Map<String, Object> build = ownedForUpdate(buildId, actor);
        validateCacheIdentity(cacheKey, sourceUpdatedAt, build);
        if (upload == null || upload.isEmpty()) throw bad("Build printout is empty.");
        if (!MediaType.IMAGE_PNG_VALUE.equalsIgnoreCase(upload.getContentType())) {
            throw bad("Build printouts must be PNG images.");
        }
        Path folder = cacheFolder();
        Path temporary = folder.resolve("." + UUID.randomUUID() + ".upload");
        try {
            Files.createDirectories(folder);
            long maximum = maximumBytes(build);
            BuildPrintoutFileValidator.Result result = BuildPrintoutFileValidator.copyAndValidate(
                    upload, temporary, maximum, imageOptimizer);
            String existingKey = RowValues.string(build, "printout_cache_key");
            String existingChecksum = RowValues.string(build, "printout_checksum");
            Path existingTarget = existingChecksum == null ? null : cachePath(buildId, existingChecksum);
            boolean existingFile = existingTarget != null && Files.isRegularFile(existingTarget);

            if (cacheKey.equals(existingKey) && existingChecksum != null
                    && !result.checksum().equals(existingChecksum)) {
                throw conflict("The same build print cache key produced different image content.");
            }
            boolean changed = !cacheKey.equals(existingKey)
                    || !result.checksum().equals(existingChecksum)
                    || !existingFile;
            if (!changed) {
                Files.deleteIfExists(temporary);
                return BuildDtoMapper.printout(false, cacheKey, result.checksum(), result.size(), sourceUpdatedAt,
                        RowValues.dateTime(build, "printout_updated_at"), url(buildId, cacheKey));
            }

            Path target = cachePath(buildId, result.checksum());
            boolean targetPreexisting = Files.isRegularFile(target);
            move(temporary, target);
            registerFileTransition(target, targetPreexisting,
                    existingTarget != null && !existingTarget.equals(target) ? existingTarget : null);
            deleteAfterCommit(legacyCachePath(buildId));

            LocalDateTime now = UtcDateTimes.now(clock);
            repository.update(BuildPrintoutQueries.SAVE_UPDATE_01,
                    Map.of("cacheKey", cacheKey, "checksum", result.checksum(), "size", result.size(),
                            "sourceUpdatedAt", sourceUpdatedAt, "now", now, "id", buildId));
            audit.record(actor, "build", buildId, "printout_update",
                    "Build printout cache updated.", List.of("printout"));
            return BuildDtoMapper.printout(true, cacheKey, result.checksum(), result.size(),
                    sourceUpdatedAt, now, url(buildId, cacheKey));
        } catch (ResponseStatusException exception) {
            deleteQuietly(temporary); throw exception;
        } catch (IOException exception) {
            deleteQuietly(temporary); throw new IllegalStateException("Could not store build printout.", exception);
        }
    }

    @Transactional(readOnly = true)
    public BinaryDownloadDto content(long buildId, String cacheKey) {
        validateCacheKey(cacheKey);
        Map<String, Object> build = repository.optional(BuildPrintoutQueries.CONTENT_SELECT_01, Map.of("id", buildId))
                .orElseThrow(BuildPrintoutService::notFound);
        if (!currentCacheMetadata(build) || !cacheKey.equals(RowValues.string(build, "printout_cache_key"))) {
            throw notFound();
        }
        String checksum = RowValues.requiredString(build, "printout_checksum");
        Path target = cachePath(buildId, checksum);
        if (!target.startsWith(root()) || !Files.isRegularFile(target)) throw notFound();
        try {
            return new BinaryDownloadDto(
                    new FileSystemResource(target),
                    MediaType.IMAGE_PNG,
                    Files.size(target),
                    null,
                    CacheControl.maxAge(CLIENT_CACHE_MAX_AGE).cachePrivate(),
                    '"' + checksum + '"');
        } catch (IOException exception) {
            throw new IllegalStateException("Could not read build printout.", exception);
        }
    }

    /** Invalidates derived cache metadata whenever the business build revision changes. */
    public void invalidate(long buildId) {
        Map<String, Object> row = repository.optional(BuildPrintoutQueries.CONTENT_SELECT_01, Map.of("id", buildId))
                .orElse(null);
        Path existing = row == null ? null : cachePathIfPresent(buildId, RowValues.string(row, "printout_checksum"));
        repository.update(BuildPrintoutQueries.CLEAR_UPDATE_01, Map.of("id", buildId));
        if (existing != null) deleteAfterCommit(existing);
        deleteAfterCommit(legacyCachePath(buildId));
    }

    /** Removes all filesystem cache variants after a build row has been deleted. */
    public void deleteAfterBuildCommit(long buildId) {
        runAfterCommit(() -> deleteBuildFiles(buildId));
    }

    @Scheduled(
            fixedDelayString = "${rbf.storage.printout-cleanup-interval:PT24H}",
            initialDelayString = "${rbf.storage.printout-cleanup-initial-delay:PT5M}")
    @Transactional
    public void cleanup() {
        Path folder = cacheFolder();
        try {
            Files.createDirectories(folder);
            Set<String> validFiles = new HashSet<>();
            int metadataCleared = 0;
            for (Map<String, Object> row : repository.query(BuildPrintoutQueries.CACHE_ROWS_SELECT_01, Map.of())) {
                long id = RowValues.longValue(row, "id");
                String checksum = RowValues.string(row, "printout_checksum");
                Path file = cachePathIfPresent(id, checksum);
                if (currentCacheMetadata(row) && file != null && Files.isRegularFile(file)) {
                    validFiles.add(file.getFileName().toString());
                } else if (clearIfUnchanged(row)) {
                    if (file != null) deleteQuietly(file);
                    metadataCleared++;
                }
            }

            int orphanFilesDeleted = 0;
            int temporaryFilesDeleted = 0;
            Instant temporaryCutoff = clock.instant().minus(TEMPORARY_MAX_AGE);
            Instant orphanCutoff = clock.instant().minus(ORPHAN_GRACE);
            try (DirectoryStream<Path> files = Files.newDirectoryStream(folder)) {
                for (Path file : files) {
                    if (!Files.isRegularFile(file)) continue;
                    String name = file.getFileName().toString();
                    Matcher cache = CACHE_FILE.matcher(name);
                    if (cache.matches()) {
                        if (!validFiles.contains(name)
                                && Files.getLastModifiedTime(file).toInstant().isBefore(orphanCutoff)
                                && Files.deleteIfExists(file)) {
                            orphanFilesDeleted++;
                        }
                        continue;
                    }
                    if (name.startsWith(".") && name.endsWith(".upload")
                            && Files.getLastModifiedTime(file).toInstant().isBefore(temporaryCutoff)
                            && Files.deleteIfExists(file)) {
                        temporaryFilesDeleted++;
                    }
                }
            }
            if (metadataCleared > 0 || orphanFilesDeleted > 0 || temporaryFilesDeleted > 0) {
                LOG.info("build_printout_cache_cleanup metadataCleared={} orphanFilesDeleted={} temporaryFilesDeleted={}",
                        metadataCleared, orphanFilesDeleted, temporaryFilesDeleted);
            }
        } catch (IOException exception) {
            LOG.warn("Build printout cache cleanup could not inspect {}", folder, exception);
        }
    }

    private boolean clearIfUnchanged(Map<String, Object> row) {
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("id", RowValues.longValue(row, "id"));
        parameters.put("cacheKey", RowValues.string(row, "printout_cache_key"));
        parameters.put("checksum", RowValues.requiredString(row, "printout_checksum"));
        parameters.put("sourceUpdatedAt", RowValues.nullableDateTime(row, "printout_source_updated_at"));
        return repository.update(BuildPrintoutQueries.CLEAR_IF_MATCH_UPDATE_01, parameters) == 1;
    }

    private void validateCacheIdentity(String cacheKey, LocalDateTime sourceUpdatedAt, Map<String, Object> build) {
        validateCacheKey(cacheKey);
        if (sourceUpdatedAt == null) throw bad("Build printout source version is required.");
        LocalDateTime currentVersion = RowValues.dateTime(build, "updated_at");
        if (!currentVersion.equals(sourceUpdatedAt)) {
            throw conflict("The build changed while the printout was being prepared. Prepare it again.");
        }
    }

    private static void validateCacheKey(String cacheKey) {
        if (cacheKey == null || !CACHE_KEY.matcher(cacheKey).matches()) {
            throw bad("Build printout cache key is invalid.");
        }
    }

    private boolean currentCacheMetadata(Map<String, Object> build) {
        LocalDateTime sourceUpdatedAt = RowValues.nullableDateTime(build, "printout_source_updated_at");
        return RowValues.string(build, "printout_cache_key") != null
                && RowValues.string(build, "printout_checksum") != null
                && sourceUpdatedAt != null
                && sourceUpdatedAt.equals(RowValues.nullableDateTime(build, "updated_at"));
    }

    private Map<String, Object> ownedForUpdate(long id, AuthenticatedUser actor) {
        Map<String, Object> row = repository.optional(BuildPrintoutQueries.CONTENT_LOCK_SELECT_01, Map.of("id", id))
                .orElseThrow(BuildPrintoutService::notFound);
        Long ownerId = RowValues.nullableLong(row, "owner_id");
        if (!actor.staff() && (ownerId == null || ownerId != actor.id())) throw notFound();
        return row;
    }

    private long maximumBytes(Map<String, Object> build) throws IOException {
        long imageLimit = mb(storage.imageLimitMb());
        long existing = RowValues.nullableLong(build, "printout_size_bytes") == null
                ? 0 : RowValues.longValue(build, "printout_size_bytes");
        long globalUsed = repository.count(BuildPrintoutQueries.GLOBAL_BYTES_SELECT_01, Map.of());
        long globalRemaining = storage.globalTotalMb() == 0 ? Long.MAX_VALUE
                : Math.max(0, mb(storage.globalTotalMb()) - Math.max(0, globalUsed - existing));
        Files.createDirectories(root());
        long diskRemaining = Math.max(0,
                Files.getFileStore(root()).getUsableSpace() - mb(storage.minimumFreeMb()));
        long maximum = Math.min(imageLimit, Math.min(globalRemaining, diskRemaining));
        if (maximum <= 0) throw bad("Build printout storage quota is exhausted or the free-space reserve was reached.");
        return maximum;
    }

    private Path root() { return storage.uploadRoot().toAbsolutePath().normalize(); }
    private Path cacheFolder() { return root().resolve("build-printouts"); }
    private Path legacyCachePath(long buildId) { return cacheFolder().resolve("build-" + buildId + ".png").normalize(); }
    private Path cachePath(long buildId, String checksum) {
        if (checksum == null || !checksum.matches("[a-f0-9]{64}")) {
            throw new IllegalStateException("Invalid persisted build printout checksum.");
        }
        return cacheFolder().resolve("build-" + buildId + "-" + checksum + ".png").normalize();
    }
    private Path cachePathIfPresent(long buildId, String checksum) {
        return checksum == null ? null : cachePath(buildId, checksum);
    }
    private static void move(Path source, Path target) throws IOException {
        try { Files.move(source, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
        catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
            Files.move(source, target, StandardCopyOption.REPLACE_EXISTING);
        }
    }
    private static long mb(long value) { return Math.multiplyExact(value, 1024L * 1024L); }
    private static void deleteQuietly(Path path) { try { Files.deleteIfExists(path); } catch (IOException ignored) { } }
    private void deleteBuildFiles(long buildId) {
        Path folder = cacheFolder();
        if (!Files.isDirectory(folder)) return;
        deleteQuietly(folder.resolve("build-" + buildId + ".png"));
        try (DirectoryStream<Path> files = Files.newDirectoryStream(folder, "build-" + buildId + "-*.png")) {
            for (Path file : files) deleteQuietly(file);
        } catch (IOException exception) {
            LOG.warn("Could not remove build printout cache files for build {}", buildId, exception);
        }
    }
    private static void deleteAfterCommit(Path path) { runAfterCommit(() -> deleteQuietly(path)); }
    private static void runAfterCommit(Runnable action) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) { action.run(); return; }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override public void afterCommit() { action.run(); }
        });
    }
    private static void registerFileTransition(Path newTarget, boolean newTargetPreexisting, Path oldTarget) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) {
            if (oldTarget != null) deleteQuietly(oldTarget);
            return;
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override public void afterCommit() {
                if (oldTarget != null) deleteQuietly(oldTarget);
            }
            @Override public void afterCompletion(int status) {
                if (status != TransactionSynchronization.STATUS_COMMITTED && !newTargetPreexisting) {
                    deleteQuietly(newTarget);
                }
            }
        });
    }
    private static String url(long id, String cacheKey) {
        return "/api/builds/" + id + "/printout?cache_key="
                + URLEncoder.encode(cacheKey, StandardCharsets.UTF_8);
    }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private static ResponseStatusException conflict(String message) { return new ResponseStatusException(CONFLICT, message); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Build printout not found."); }
}
