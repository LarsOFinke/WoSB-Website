package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.repository.BuildDataRepository;
import eu.royalblackwater.api.builds.repository.queries.BuildPrintoutQueries;
import eu.royalblackwater.api.config.StorageProperties;
import eu.royalblackwater.api.dto.BuildPrintoutRead;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class BuildPrintoutServiceTest {
    private static final LocalDateTime BUILD_VERSION = LocalDateTime.of(2026, 8, 8, 10, 0);
    private static final String CACHE_KEY = "print-v3:" + "a".repeat(64);
    private static final AuthenticatedUser OWNER = new AuthenticatedUser(7, "owner", "user", false, false, false);

    @TempDir
    Path temporaryRoot;

    @Test
    void saveKeepsBusinessBuildVersionSeparateFromCacheMetadata() throws Exception {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        when(repository.optional(BuildPrintoutQueries.CONTENT_LOCK_SELECT_01, Map.of("id", 42L)))
                .thenReturn(Optional.of(buildRow()));
        when(repository.count(BuildPrintoutQueries.GLOBAL_BYTES_SELECT_01, Map.of())).thenReturn(0L);

        BuildPrintoutRead result = service.save(42L, png(), CACHE_KEY, BUILD_VERSION, OWNER);

        assertTrue(result.changed());
        assertEquals(CACHE_KEY, result.cacheKey());
        assertEquals(BUILD_VERSION, result.sourceUpdatedAt());
        String checksum = sha256(pngBytes());
        assertTrue(Files.isRegularFile(temporaryRoot.resolve("build-printouts/build-42-" + checksum + ".png")));
        assertTrue(result.url().contains("cache_key=print-v3%3A"));
        verify(repository).update(eq(BuildPrintoutQueries.SAVE_UPDATE_01), org.mockito.ArgumentMatchers.argThat(values ->
                CACHE_KEY.equals(values.get("cacheKey"))
                        && BUILD_VERSION.equals(values.get("sourceUpdatedAt"))
                        && Long.valueOf(42L).equals(values.get("id"))));
        assertFalse(BuildPrintoutQueries.SAVE_UPDATE_01.matches("(?s).*[^_]updated_at\\s*=\\s*:now.*"),
                "saving a derived printout must not bump builds.updated_at");
    }

    @Test
    void saveRejectsAStaleBuildRevisionBeforeWriting() {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        when(repository.optional(BuildPrintoutQueries.CONTENT_LOCK_SELECT_01, Map.of("id", 42L)))
                .thenReturn(Optional.of(buildRow()));

        ResponseStatusException error = assertThrows(ResponseStatusException.class,
                () -> service.save(42L, png(), CACHE_KEY, BUILD_VERSION.minusSeconds(1), OWNER));

        assertEquals(409, error.getStatusCode().value());
        verify(repository, never()).update(eq(BuildPrintoutQueries.SAVE_UPDATE_01), anyMap());
    }

    @Test
    void contentRequiresTheCurrentVersionedCacheKey() throws Exception {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        String checksum = sha256(pngBytes());
        Map<String, Object> row = buildRow();
        row.put("printout_cache_key", CACHE_KEY);
        row.put("printout_checksum", checksum);
        row.put("printout_source_updated_at", BUILD_VERSION);
        when(repository.optional(BuildPrintoutQueries.CONTENT_SELECT_01, Map.of("id", 42L)))
                .thenReturn(Optional.of(row));
        Path folder = temporaryRoot.resolve("build-printouts");
        Files.createDirectories(folder);
        Files.write(folder.resolve("build-42-" + checksum + ".png"), pngBytes());

        assertEquals(pngBytes().length, service.content(42L, CACHE_KEY).contentLength());
        ResponseStatusException error = assertThrows(ResponseStatusException.class,
                () -> service.content(42L, "print-v3:" + "b".repeat(64)));
        assertEquals(404, error.getStatusCode().value());
    }

    @Test
    void sameCacheKeyCannotBeReplacedByDifferentPngBytes() throws Exception {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        Map<String, Object> row = buildRow();
        row.put("printout_cache_key", CACHE_KEY);
        row.put("printout_checksum", "f".repeat(64));
        row.put("printout_source_updated_at", BUILD_VERSION);
        when(repository.optional(BuildPrintoutQueries.CONTENT_LOCK_SELECT_01, Map.of("id", 42L)))
                .thenReturn(Optional.of(row));
        when(repository.count(BuildPrintoutQueries.GLOBAL_BYTES_SELECT_01, Map.of())).thenReturn(0L);

        ResponseStatusException error = assertThrows(ResponseStatusException.class,
                () -> service.save(42L, png(), CACHE_KEY, BUILD_VERSION, OWNER));

        assertEquals(409, error.getStatusCode().value());
        verify(repository, never()).update(eq(BuildPrintoutQueries.SAVE_UPDATE_01), anyMap());
    }

    @Test
    void saveReusesAnExistingMatchingCacheEntryWithoutPersistingOrAuditingAgain() throws Exception {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        String checksum = sha256(pngBytes());
        Map<String, Object> row = buildRow();
        row.put("printout_cache_key", CACHE_KEY);
        row.put("printout_checksum", checksum);
        row.put("printout_source_updated_at", BUILD_VERSION);
        row.put("printout_updated_at", BUILD_VERSION.plusMinutes(1));
        when(repository.optional(BuildPrintoutQueries.CONTENT_LOCK_SELECT_01, Map.of("id", 42L)))
                .thenReturn(Optional.of(row));
        when(repository.count(BuildPrintoutQueries.GLOBAL_BYTES_SELECT_01, Map.of())).thenReturn((long) pngBytes().length);
        Path folder = temporaryRoot.resolve("build-printouts");
        Files.createDirectories(folder);
        Files.write(folder.resolve("build-42-" + checksum + ".png"), pngBytes());

        BuildPrintoutRead result = service.save(42L, png(), CACHE_KEY, BUILD_VERSION, OWNER);

        assertFalse(result.changed());
        assertEquals(checksum, result.checksum());
        verify(repository, never()).update(eq(BuildPrintoutQueries.SAVE_UPDATE_01), anyMap());
        verifyNoInteractions(audit);
    }

    @Test
    void invalidateClearsMetadataAndDeletesTheDerivedCacheFile() throws Exception {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        String checksum = sha256(pngBytes());
        Map<String, Object> row = buildRow();
        row.put("printout_checksum", checksum);
        when(repository.optional(BuildPrintoutQueries.CONTENT_SELECT_01, Map.of("id", 42L)))
                .thenReturn(Optional.of(row));
        Path folder = temporaryRoot.resolve("build-printouts");
        Files.createDirectories(folder);
        Path cached = folder.resolve("build-42-" + checksum + ".png");
        Files.write(cached, pngBytes());

        service.invalidate(42L);

        verify(repository).update(BuildPrintoutQueries.CLEAR_UPDATE_01, Map.of("id", 42L));
        assertFalse(Files.exists(cached));
    }

    @Test
    void cleanupDeletesOrphanedServerWideCacheFiles() throws Exception {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        Path folder = temporaryRoot.resolve("build-printouts");
        Files.createDirectories(folder);
        Path orphan = folder.resolve("build-999.png");
        Files.write(orphan, pngBytes());
        Files.setLastModifiedTime(orphan, java.nio.file.attribute.FileTime.from(Instant.parse("2026-08-08T08:00:00Z")));
        when(repository.query(BuildPrintoutQueries.CACHE_ROWS_SELECT_01, Map.of())).thenReturn(java.util.List.of());

        service.cleanup();

        assertFalse(Files.exists(orphan));
    }

    @Test
    void cleanupKeepsFreshUncommittedLookingCacheFilesDuringGraceWindow() throws Exception {
        BuildDataRepository repository = mock(BuildDataRepository.class);
        AuditService audit = mock(AuditService.class);
        BuildPrintoutService service = service(repository, audit);
        Path folder = temporaryRoot.resolve("build-printouts");
        Files.createDirectories(folder);
        Path recent = folder.resolve("build-42-" + "a".repeat(64) + ".png");
        Files.write(recent, pngBytes());
        Files.setLastModifiedTime(recent, java.nio.file.attribute.FileTime.from(Instant.parse("2026-08-08T10:04:00Z")));
        when(repository.query(BuildPrintoutQueries.CACHE_ROWS_SELECT_01, Map.of())).thenReturn(java.util.List.of());

        service.cleanup();

        assertTrue(Files.exists(recent));
    }

    private BuildPrintoutService service(BuildDataRepository repository, AuditService audit) {
        StorageProperties storage = new StorageProperties(temporaryRoot, 12, 24, 50, 250, 4096, 0);
        Clock clock = Clock.fixed(Instant.parse("2026-08-08T10:05:00Z"), ZoneOffset.UTC);
        return new BuildPrintoutService(repository, storage, audit, clock);
    }

    private static Map<String, Object> buildRow() {
        return new java.util.HashMap<>(Map.of(
                "id", 42L,
                "owner_id", 7L,
                "updated_at", BUILD_VERSION,
                "printout_size_bytes", 0L));
    }

    private static MockMultipartFile png() {
        return new MockMultipartFile("image", "build-42.png", "image/png", pngBytes());
    }

    private static String sha256(byte[] value) {
        try {
            return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(value));
        } catch (java.security.NoSuchAlgorithmException exception) {
            throw new IllegalStateException(exception);
        }
    }

    private static byte[] pngBytes() {
        byte[] value = new byte[24];
        byte[] signature = {(byte) 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a};
        System.arraycopy(signature, 0, value, 0, signature.length);
        value[12] = 'I'; value[13] = 'H'; value[14] = 'D'; value[15] = 'R';
        ByteBuffer.wrap(value, 16, 8).order(ByteOrder.BIG_ENDIAN).putInt(1400).putInt(1980);
        return value;
    }
}
