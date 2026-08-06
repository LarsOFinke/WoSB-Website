package eu.royalblackwater.api.files.service;

import eu.royalblackwater.api.config.StorageProperties;
import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.files.dto.StoredFileDto;
import eu.royalblackwater.api.files.mapper.FileDtoMapper;
import eu.royalblackwater.api.files.repository.FileAssetRepository;
import eu.royalblackwater.api.files.repository.queries.FileAssetQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.shared.dto.BinaryDownloadDto;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.CacheControl;
import org.springframework.http.ContentDisposition;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class FileAssetService {
    private static final Set<String> CONTEXTS = Set.of("general", "forum", "guide", "master-data");
    private final FileAssetRepository repository;
    private final StorageProperties properties;
    private final Clock clock;

    public FileAssetService(FileAssetRepository repository, StorageProperties properties, Clock clock) {
        this.repository = repository;
        this.properties = properties;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<FileRead> list(long ownerId, String context) {
        StringBuilder sql = new StringBuilder(FileAssetQueries.LIST_SELECT_01);
        Map<String, Object> parameters = new LinkedHashMap<>(Map.of("ownerId", ownerId));
        if (context != null && !context.isBlank()) {
            sql.append(FileAssetQueries.LIST_AND_01);
            parameters.put("context", normalizeContext(context));
        }
        sql.append(FileAssetQueries.LIST_ORDER_BY_01);
        return repository.query(sql.toString(), parameters).stream().map(FileDtoMapper::read).toList();
    }

    @Transactional
    public FileRead upload(MultipartFile upload, String context, AuthenticatedUser owner) {
        if (upload == null || upload.isEmpty()) throw bad("Empty files cannot be uploaded.");
        String normalizedContext = normalizeContext(context);
        if ("master-data".equals(normalizedContext) && !owner.isAdmin()) {
            throw new ResponseStatusException(FORBIDDEN, "Only administrators can upload master-data assets.");
        }
        String extension = FileTypePolicy.extension(upload.getOriginalFilename());
        String declaredType = normalizedType(upload.getContentType());
        long maximum = effectiveLimit(owner.id(), declaredType);
        LocalDateTime createdAt = now();
        Path root = normalizedRoot();
        Path folder = root.resolve(String.format("%04d/%02d", createdAt.getYear(), createdAt.getMonthValue()));
        String storedName = UUID.randomUUID().toString().replace("-", "") + extension;
        Path target = folder.resolve(storedName);
        Path temporary = folder.resolve("." + storedName + ".upload");
        try {
            Files.createDirectories(folder);
            copyLimited(upload, temporary, maximum);
            String detectedType = FileTypePolicy.validate(temporary, extension, declaredType);
            moveAtomically(temporary, target);
            registerRollbackCleanup(target);
            String relativePath = root.relativize(target).toString().replace('\\', '/');
            long id = repository.insertReturningId(FileAssetQueries.UPLOAD_INSERT_01, Map.of(
                            "ownerId", owner.id(), "originalName", safeOriginalName(upload, storedName),
                            "storedName", storedName, "relativePath", relativePath, "mimeType", detectedType,
                            "sizeBytes", Files.size(target), "context", normalizedContext,
                            "public", "master-data".equals(normalizedContext), "createdAt", createdAt));
            return required(id);
        } catch (ResponseStatusException exception) {
            deleteQuietly(temporary); deleteQuietly(target); throw exception;
        } catch (IOException exception) {
            deleteQuietly(temporary); deleteQuietly(target);
            throw new IllegalStateException("Could not store uploaded file.", exception);
        }
    }

    @Transactional
    public void delete(long fileId, AuthenticatedUser actor) {
        Map<String, Object> file = raw(fileId);
        Long ownerId = RowValues.nullableLong(file, "owner_id");
        if ((ownerId == null || ownerId != actor.id()) && !actor.staff()) {
            throw new ResponseStatusException(NOT_FOUND, "File not found.");
        }
        if (isReferenced(fileId)) throw bad("Referenced files cannot be deleted directly.");
        Path path = resolve(file);
        repository.update(FileAssetQueries.DELETE_DELETE_01, Map.of("id", fileId));
        registerCommitCleanup(path);
    }

    @Transactional(readOnly = true)
    public BinaryDownloadDto content(long fileId, AuthenticatedUser actor) {
        Map<String, Object> file = raw(fileId);
        boolean publicFile = RowValues.booleanValue(file, "is_public");
        Long ownerId = RowValues.nullableLong(file, "owner_id");
        if (!publicFile && (actor == null || (ownerId != null && ownerId != actor.id() && !actor.staff()))) {
            throw new ResponseStatusException(actor == null ? org.springframework.http.HttpStatus.UNAUTHORIZED : FORBIDDEN,
                    actor == null ? "Login required." : "File access denied.");
        }
        Path path = resolve(file);
        if (!Files.isRegularFile(path)) throw new ResponseStatusException(NOT_FOUND, "File not found.");
        return new BinaryDownloadDto(
                new FileSystemResource(path),
                MediaType.parseMediaType(RowValues.requiredString(file, "mime_type")),
                RowValues.longValue(file, "size_bytes"),
                ContentDisposition.inline()
                        .filename(RowValues.requiredString(file, "original_name"),
                                java.nio.charset.StandardCharsets.UTF_8)
                        .build(),
                publicFile ? CacheControl.maxAge(java.time.Duration.ofHours(1)).cachePublic()
                        : CacheControl.noStore().cachePrivate(),
                null);
    }

    @Transactional(readOnly = true)
    public List<StoredFileDto> ownedFiles(List<Long> ids, AuthenticatedUser actor) {
        List<Long> normalized = distinctPositive(ids);
        if (normalized.isEmpty()) return List.of();
        List<Map<String, Object>> rows = repository.query(FileAssetQueries.OWNED_FILES_SELECT_01, Map.of("ids", normalized));
        Map<Long, Map<String, Object>> byId = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) byId.put(RowValues.longValue(row, "id"), row);
        if (byId.size() != normalized.size()) throw bad("One or more selected files do not exist.");
        for (Map<String, Object> row : rows) {
            Long ownerId = RowValues.nullableLong(row, "owner_id");
            if (ownerId != null && ownerId != actor.id() && !actor.staff()) {
                throw bad("One or more selected files are not owned by you.");
            }
        }
        return normalized.stream()
                .map(byId::get)
                .map(FileDtoMapper::stored)
                .toList();
    }

    public void attach(String table, String ownerColumn, long ownerId, List<StoredFileDto> files, String context) {
        assertAttachmentTable(table, ownerColumn);
        repository.update(FileAssetQueries.ATTACH_DELETE_01 + table + FileAssetQueries.ATTACH_WHERE_01 + ownerColumn + "=:ownerId", Map.of("ownerId", ownerId));
        int order = 0;
        for (StoredFileDto file : files) {
            long fileId = file.id();
            repository.update(FileAssetQueries.ATTACH_INSERT_01 + table + "(" + ownerColumn + ",file_id,sort_order) values(:ownerId,:fileId,:sortOrder)",
                    Map.of("ownerId", ownerId, "fileId", fileId, "sortOrder", order++));
            repository.update(FileAssetQueries.ATTACH_UPDATE_01,
                    Map.of("context", normalizeContext(context), "id", fileId));
        }
    }

    @Transactional(readOnly = true)
    public List<FileRead> attachments(String table, String ownerColumn, long ownerId) {
        assertAttachmentTable(table, ownerColumn);
        return repository.query(FileAssetQueries.ATTACHMENTS_SELECT_01 + table + " a join stored_files f on f.id=a.file_id where a."
                        + ownerColumn + "=:ownerId order by a.sort_order,a.id", Map.of("ownerId", ownerId))
                .stream().map(FileDtoMapper::read).toList();
    }

    @Transactional(readOnly = true)
    public Map<Long, List<FileRead>> attachmentsByOwners(String table, String ownerColumn, List<Long> ownerIds) {
        assertAttachmentTable(table, ownerColumn);
        List<Long> normalized = distinctPositive(ownerIds);
        if (normalized.isEmpty()) return Map.of();
        Map<Long, List<FileRead>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : repository.query(FileAssetQueries.ATTACHMENTS_BY_OWNERS_SELECT_01 + ownerColumn + " owner_id,f.* from " + table
                + " a join stored_files f on f.id=a.file_id where a." + ownerColumn
                + " in (:ownerIds) order by a." + ownerColumn + ",a.sort_order,a.id", Map.of("ownerIds", normalized))) {
            long ownerId = RowValues.longValue(row, "owner_id");
            result.computeIfAbsent(ownerId, ignored -> new ArrayList<>()).add(FileDtoMapper.read(row));
        }
        result.replaceAll((ignored, values) -> List.copyOf(values));
        return Map.copyOf(result);
    }

    public void refreshPublication(Set<Long> ids) {
        for (Long id : distinctPositive(new ArrayList<>(ids))) {
            boolean referenced = repository.count(FileAssetQueries.REFRESH_PUBLICATION_SELECT_01, Map.of("id", id)) > 0;
            repository.update(FileAssetQueries.REFRESH_PUBLICATION_UPDATE_01,
                    Map.of("referenced", referenced, "id", id));
        }
    }

    private FileRead required(long id) { return FileDtoMapper.read(raw(id)); }
    private Map<String, Object> raw(long id) {
        return repository.optional(FileAssetQueries.RAW_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "File not found."));
    }

    private boolean isReferenced(long id) {
        return repository.count(FileAssetQueries.IS_REFERENCED_SELECT_01, Map.of("id", id)) > 0;
    }

    private long effectiveLimit(long ownerId, String mimeType) {
        long typeLimit = mb(mimeType.startsWith("image/") ? properties.imageLimitMb()
                : Set.of("application/pdf", "text/plain").contains(mimeType)
                ? properties.documentLimitMb() : properties.videoLimitMb());
        long ownerUsed = repository.count(FileAssetQueries.EFFECTIVE_LIMIT_SELECT_01, Map.of("id", ownerId));
        long globalUsed = repository.count(FileAssetQueries.EFFECTIVE_LIMIT_SELECT_02, Map.of());
        long userRemaining = properties.perUserTotalMb() == 0 ? Long.MAX_VALUE : Math.max(0, mb(properties.perUserTotalMb()) - ownerUsed);
        long globalRemaining = properties.globalTotalMb() == 0 ? Long.MAX_VALUE : Math.max(0, mb(properties.globalTotalMb()) - globalUsed);
        try {
            Files.createDirectories(normalizedRoot());
            long diskRemaining = Math.max(0, Files.getFileStore(normalizedRoot()).getUsableSpace() - mb(properties.minimumFreeMb()));
            long maximum = Math.min(typeLimit, Math.min(userRemaining, Math.min(globalRemaining, diskRemaining)));
            if (maximum <= 0) throw bad("Upload storage quota is exhausted or the free-space reserve was reached.");
            return maximum;
        } catch (IOException exception) {
            throw new IllegalStateException("Could not inspect upload storage capacity.", exception);
        }
    }

    private static void moveAtomically(Path source, Path target) throws IOException {
        try { Files.move(source, target, StandardCopyOption.ATOMIC_MOVE); }
        catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
            Files.move(source, target);
        }
    }

    private static void copyLimited(MultipartFile upload, Path target, long maximum) throws IOException {
        long size = 0;
        try (InputStream input = upload.getInputStream(); OutputStream output = Files.newOutputStream(target,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            byte[] buffer = new byte[1024 * 1024];
            int count;
            while ((count = input.read(buffer)) >= 0) {
                if (count == 0) continue;
                size += count;
                if (size > maximum) throw bad("File is too large or exceeds the remaining quota.");
                output.write(buffer, 0, count);
            }
        }
        if (size == 0) throw bad("Empty files cannot be uploaded.");
    }

    private Path normalizedRoot() { return properties.uploadRoot().toAbsolutePath().normalize(); }
    private Path resolve(Map<String, Object> file) {
        Path root = normalizedRoot();
        Path candidate = root.resolve(RowValues.requiredString(file, "relative_path")).normalize();
        if (!candidate.startsWith(root)) throw new ResponseStatusException(NOT_FOUND, "File not found.");
        return candidate;
    }


    private static String normalizeContext(String value) {
        String normalized = value == null || value.isBlank() ? "general" : value.strip().toLowerCase(java.util.Locale.ROOT);
        if (!CONTEXTS.contains(normalized)) throw bad("Unsupported upload usage context.");
        return normalized;
    }

    private static String normalizedType(String value) { return value == null ? "" : value.split(";", 2)[0].strip().toLowerCase(); }
    private static String safeOriginalName(MultipartFile upload, String fallback) {
        String value = upload.getOriginalFilename();
        if (value == null || value.isBlank()) return fallback;
        String name = Path.of(value).getFileName().toString();
        return name.length() > 255 ? name.substring(0, 255) : name;
    }
    private static List<Long> distinctPositive(List<Long> ids) {
        if (ids == null) return List.of();
        LinkedHashSet<Long> values = new LinkedHashSet<>();
        for (Long id : ids) if (id != null && id > 0) values.add(id);
        return List.copyOf(values);
    }
    private static void assertAttachmentTable(String table, String ownerColumn) {
        boolean allowed = ("forum_post_attachments".equals(table) && "post_id".equals(ownerColumn))
                || ("guide_attachments".equals(table) && "guide_id".equals(ownerColumn));
        if (!allowed) throw new IllegalArgumentException("Unsupported attachment relation.");
    }
    private static long mb(long value) { return Math.multiplyExact(value, 1024L * 1024L); }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static void deleteQuietly(Path path) { try { Files.deleteIfExists(path); } catch (IOException ignored) { } }
    private static void registerRollbackCleanup(Path path) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) return;
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override public void afterCompletion(int status) {
                if (status != STATUS_COMMITTED) deleteQuietly(path);
            }
        });
    }
    private static void registerCommitCleanup(Path path) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) { deleteQuietly(path); return; }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override public void afterCommit() { deleteQuietly(path); }
        });
    }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
