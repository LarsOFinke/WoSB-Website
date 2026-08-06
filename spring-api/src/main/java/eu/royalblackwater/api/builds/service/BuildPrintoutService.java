package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.mapper.BuildDtoMapper;
import eu.royalblackwater.api.builds.repository.BuildDataRepository;
import eu.royalblackwater.api.builds.repository.queries.BuildPrintoutQueries;
import eu.royalblackwater.api.config.StorageProperties;
import eu.royalblackwater.api.dto.BuildPrintoutRead;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.shared.dto.BinaryDownloadDto;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.CacheControl;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class BuildPrintoutService {
    private static final byte[] PNG = {(byte) 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a};
    private final BuildDataRepository repository;
    private final StorageProperties storage;
    private final AuditService audit;
    private final Clock clock;

    BuildPrintoutService(BuildDataRepository repository, StorageProperties storage, AuditService audit, Clock clock) {
        this.repository = repository; this.storage = storage; this.audit = audit; this.clock = clock;
    }

    @Transactional
    public BuildPrintoutRead save(long buildId, MultipartFile upload, AuthenticatedUser actor) {
        Map<String, Object> build = owned(buildId, actor);
        if (upload == null || upload.isEmpty()) throw bad("Build printout is empty.");
        if (!MediaType.IMAGE_PNG_VALUE.equalsIgnoreCase(upload.getContentType())) throw bad("Build printouts must be PNG images.");
        Path folder = root().resolve("build-printouts");
        Path target = folder.resolve("build-" + buildId + ".png");
        Path temporary = folder.resolve("." + UUID.randomUUID() + ".upload");
        try {
            Files.createDirectories(folder);
            Result result = copyAndValidate(upload, temporary, storage.imageLimitMb() * 1024L * 1024L);
            boolean changed = !result.checksum().equals(RowValues.string(build, "printout_checksum")) || !Files.isRegularFile(target);
            if (changed) {
                move(temporary, target);
                LocalDateTime now = now();
                repository.update(BuildPrintoutQueries.SAVE_UPDATE_01, Map.of("checksum", result.checksum(), "size", result.size(), "now", now, "id", buildId));
                audit.record(actor, "build", buildId, "printout_update", "Build printout updated.", List.of("printout"));
                return BuildDtoMapper.printout(true, result.checksum(), result.size(), now, url(buildId));
            }
            Files.deleteIfExists(temporary);
            return BuildDtoMapper.printout(false, result.checksum(), result.size(),
                    RowValues.dateTime(build, "printout_updated_at"), url(buildId));
        } catch (ResponseStatusException exception) {
            delete(temporary); throw exception;
        } catch (IOException exception) {
            delete(temporary); throw new IllegalStateException("Could not store build printout.", exception);
        }
    }

    @Transactional(readOnly = true)
    public BinaryDownloadDto content(long buildId) {
        Map<String, Object> build = repository.optional(BuildPrintoutQueries.CONTENT_SELECT_01, Map.of("id", buildId))
                .orElseThrow(BuildPrintoutService::notFound);
        if (RowValues.string(build, "printout_checksum") == null) throw notFound();
        Path target = root().resolve("build-printouts/build-" + buildId + ".png").normalize();
        if (!target.startsWith(root()) || !Files.isRegularFile(target)) throw notFound();
        try {
            return new BinaryDownloadDto(
                    new FileSystemResource(target),
                    MediaType.IMAGE_PNG,
                    Files.size(target),
                    null,
                    CacheControl.noCache(),
                    '"' + RowValues.requiredString(build, "printout_checksum") + '"');
        } catch (IOException exception) {
            throw new IllegalStateException("Could not read build printout.", exception);
        }
    }

    private Map<String, Object> owned(long id, AuthenticatedUser actor) {
        Map<String, Object> row = repository.optional(BuildPrintoutQueries.CONTENT_SELECT_01, Map.of("id", id))
                .orElseThrow(BuildPrintoutService::notFound);
        Long ownerId = RowValues.nullableLong(row, "owner_id");
        if (!actor.staff() && (ownerId == null || ownerId != actor.id())) throw notFound();
        return row;
    }

    private Result copyAndValidate(MultipartFile upload, Path target, long maximum) throws IOException {
        MessageDigest digest = sha256();
        byte[] header = new byte[24];
        int headerSize = 0;
        long size = 0;
        try (InputStream input = upload.getInputStream(); OutputStream output = Files.newOutputStream(target,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            byte[] buffer = new byte[1024 * 1024];
            int count;
            while ((count = input.read(buffer)) >= 0) {
                if (count == 0) continue;
                if (headerSize < header.length) {
                    int copy = Math.min(count, header.length - headerSize);
                    System.arraycopy(buffer, 0, header, headerSize, copy); headerSize += copy;
                }
                size += count;
                if (size > maximum) throw bad("Build printout exceeds the configured image limit.");
                digest.update(buffer, 0, count); output.write(buffer, 0, count);
            }
        }
        validateHeader(header, headerSize);
        return new Result(HexFormat.of().formatHex(digest.digest()), size);
    }

    private static void validateHeader(byte[] header, int size) {
        if (size < 24) throw bad("Build printout content is not a valid PNG image.");
        for (int index = 0; index < PNG.length; index++) if (header[index] != PNG[index]) throw bad("Build printout content is not a valid PNG image.");
        if (header[12] != 'I' || header[13] != 'H' || header[14] != 'D' || header[15] != 'R') throw bad("Build printout content is not a valid PNG image.");
        ByteBuffer values = ByteBuffer.wrap(header, 16, 8).order(ByteOrder.BIG_ENDIAN);
        int width = values.getInt(); int height = values.getInt();
        if (width < 1 || width > 10_000 || height < 1 || height > 20_000) throw bad("Build printout dimensions are invalid.");
    }

    private Path root() { return storage.uploadRoot().toAbsolutePath().normalize(); }
    private static void move(Path source, Path target) throws IOException {
        try { Files.move(source, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
        catch (java.nio.file.AtomicMoveNotSupportedException ignored) { Files.move(source, target, StandardCopyOption.REPLACE_EXISTING); }
    }
    private static MessageDigest sha256() { try { return MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException exception) { throw new IllegalStateException(exception); } }
    private static void delete(Path path) { try { Files.deleteIfExists(path); } catch (IOException ignored) { } }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static String url(long id) { return "/api/builds/" + id + "/printout"; }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Build printout not found."); }
    private record Result(String checksum, long size) { }
}
