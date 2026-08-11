package eu.royalblackwater.api.files;

import eu.royalblackwater.api.config.StorageProperties;
import eu.royalblackwater.api.files.dto.StoredFileDto;
import eu.royalblackwater.api.files.repository.FileAssetRepository;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.files.service.ImageAssetOptimizer;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class FileAssetServiceCoverageTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser OWNER = new AuthenticatedUser(7, "captain", "member", false, false, false);
    private static final AuthenticatedUser STAFF = new AuthenticatedUser(8, "staff", "moderator", true, true, false);

    @TempDir Path root;

    @Test
    void uploadCoversSuccessfulTextStorageAndMasterDataAuthorization() throws Exception {
        FileAssetRepository repository = mock(FileAssetRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        when(repository.insertReturningId(anyString(), anyMap())).thenReturn(11L);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(11L, 7L, false, "stored/note.txt")));
        FileAssetService service = service(repository);
        MultipartFile upload = mock(MultipartFile.class);
        when(upload.isEmpty()).thenReturn(false);
        when(upload.getOriginalFilename()).thenReturn("../Captain notes.TXT");
        when(upload.getContentType()).thenReturn("text/plain; charset=utf-8");
        when(upload.getInputStream()).thenAnswer(ignored -> new ByteArrayInputStream("hello fleet".getBytes(StandardCharsets.UTF_8)));

        var stored = service.upload(upload, " forum ", OWNER);

        assertThat(stored.id()).isEqualTo(11L);
        verify(repository).insertReturningId(anyString(), anyMap());

        assertThatThrownBy(() -> service.upload(upload, "master-data", OWNER))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("Only administrators");
    }

    @Test
    void uploadRoutesValidatedImagesThroughTheSharedOptimizer() throws Exception {
        FileAssetRepository repository = mock(FileAssetRepository.class);
        ImageAssetOptimizer optimizer = mock(ImageAssetOptimizer.class);
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        when(repository.insertReturningId(anyString(), anyMap())).thenReturn(12L);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(12L, 7L, false, "stored/map.png")));
        FileAssetService service = new FileAssetService(repository,
                new StorageProperties(root, 12, 24, 50, 250, 4096, 0), optimizer, CLOCK);
        MockMultipartFile upload = new MockMultipartFile("file", "map.png", "image/png", validPng());

        service.upload(upload, "strategy", OWNER);

        verify(optimizer).optimize(org.mockito.ArgumentMatchers.any(Path.class), eq("image/png"));
    }

    @Test
    void listOwnedFilesAttachmentsAndPublicationCoverEmptyAndPopulatedPaths() {
        FileAssetRepository repository = mock(FileAssetRepository.class);
        Map<String, Object> row1 = fileRow(1L, 7L, false, "a.txt");
        Map<String, Object> row2 = fileRow(2L, null, true, "b.txt");
        when(repository.query(anyString(), anyMap())).thenReturn(List.of(row1, row2));
        FileAssetService service = service(repository);

        assertThat(service.list(7L, null)).hasSize(2);
        assertThat(service.list(7L, " forum ")).hasSize(2);
        assertThat(service.ownedFiles(java.util.Arrays.asList(null, -1L, 1L, 1L, 2L), OWNER)).hasSize(2);
        assertThat(service.attachments("forum_post_attachments", "post_id", 9L)).hasSize(2);
        assertThat(service.attachmentsByOwners("guide_attachments", "guide_id", List.of())).isEmpty();
        Map<String, Object> owner9 = fileRow(1L, 9L, false, "a.txt");
        Map<String, Object> owner10 = fileRow(2L, 10L, true, "b.txt");
        when(repository.query(anyString(), anyMap())).thenReturn(List.of(owner9, owner10));
        assertThat(service.attachmentsByOwners("guide_attachments", "guide_id", List.of(9L, 10L))).hasSize(2);

        service.attach("forum_post_attachments", "post_id", 9L,
                List.of(new StoredFileDto(1L, 7L), new StoredFileDto(2L, null)), "guide");

        when(repository.count(anyString(), anyMap())).thenReturn(1L, 0L);
        service.refreshPublication(Set.of(1L, 2L));
        verify(repository, org.mockito.Mockito.atLeast(1)).update(anyString(), anyMap());
    }

    @Test
    void ownedFilesRejectMissingAndForeignRows() {
        FileAssetRepository missing = mock(FileAssetRepository.class);
        when(missing.query(anyString(), anyMap())).thenReturn(List.of(fileRow(1L, 7L, false, "a.txt")));
        assertThatThrownBy(() -> service(missing).ownedFiles(List.of(1L, 2L), OWNER))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("do not exist");

        FileAssetRepository foreign = mock(FileAssetRepository.class);
        when(foreign.query(anyString(), anyMap())).thenReturn(List.of(fileRow(1L, 99L, false, "a.txt")));
        assertThatThrownBy(() -> service(foreign).ownedFiles(List.of(1L), OWNER))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("not owned by you");
        assertThat(service(foreign).ownedFiles(List.of(1L), STAFF)).hasSize(1);
    }

    @Test
    void contentCoversPublicPrivateOwnerStaffMissingAndTraversalBoundaries() throws Exception {
        Path publicPath = root.resolve("public.txt");
        Files.writeString(publicPath, "public");
        FileAssetRepository publicRepository = mock(FileAssetRepository.class);
        when(publicRepository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(1L, null, true, "public.txt")));
        assertThat(service(publicRepository).content(1L, null).resource().exists()).isTrue();

        Path privatePath = root.resolve("private.txt");
        Files.writeString(privatePath, "private");
        FileAssetRepository privateRepository = mock(FileAssetRepository.class);
        when(privateRepository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(2L, 7L, false, "private.txt")));
        assertThat(service(privateRepository).content(2L, OWNER).resource().exists()).isTrue();
        assertThat(service(privateRepository).content(2L, STAFF).resource().exists()).isTrue();
        assertThatThrownBy(() -> service(privateRepository).content(2L, null))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(401));

        FileAssetRepository foreignRepository = mock(FileAssetRepository.class);
        when(foreignRepository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(3L, 99L, false, "private.txt")));
        assertThatThrownBy(() -> service(foreignRepository).content(3L, OWNER))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(403));

        FileAssetRepository missingRepository = mock(FileAssetRepository.class);
        when(missingRepository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(4L, null, true, "missing.txt")));
        assertThatThrownBy(() -> service(missingRepository).content(4L, null))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("File not found");

        FileAssetRepository traversalRepository = mock(FileAssetRepository.class);
        when(traversalRepository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(5L, null, true, "../outside.txt")));
        assertThatThrownBy(() -> service(traversalRepository).content(5L, null))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("File not found");
    }

    @Test
    void deleteCoversOwnershipReferenceAndCommitCleanup() throws Exception {
        Path path = root.resolve("delete.txt");
        Files.writeString(path, "delete");
        FileAssetRepository repository = mock(FileAssetRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(1L, 7L, false, "delete.txt")));
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        service(repository).delete(1L, OWNER);
        assertThat(path).doesNotExist();

        FileAssetRepository referenced = mock(FileAssetRepository.class);
        when(referenced.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(2L, 7L, false, "delete.txt")));
        when(referenced.count(anyString(), anyMap())).thenReturn(1L);
        assertThatThrownBy(() -> service(referenced).delete(2L, OWNER))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("Referenced files");

        FileAssetRepository hidden = mock(FileAssetRepository.class);
        when(hidden.optional(anyString(), anyMap())).thenReturn(Optional.of(fileRow(3L, 99L, false, "delete.txt")));
        assertThatThrownBy(() -> service(hidden).delete(3L, OWNER))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(404));
    }

    private FileAssetService service(FileAssetRepository repository) {
        return new FileAssetService(repository, new StorageProperties(root, 12, 24, 50, 250, 4096, 0),
                new ImageAssetOptimizer(), CLOCK);
    }

    private static Map<String, Object> fileRow(long id, Long ownerId, boolean isPublic, String relativePath) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", id);
        row.put("owner_id", ownerId);
        row.put("is_public", isPublic);
        row.put("mime_type", "text/plain");
        row.put("original_name", "note.txt");
        row.put("relative_path", relativePath);
        row.put("size_bytes", 6L);
        row.put("stored_name", "stored.txt");
        row.put("usage_context", "general");
        row.put("created_at", LocalDateTime.of(2030, 1, 15, 12, 0));
        return row;
    }

    private static byte[] validPng() throws Exception {
        java.awt.image.BufferedImage image = new java.awt.image.BufferedImage(8, 8,
                java.awt.image.BufferedImage.TYPE_INT_ARGB);
        java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream();
        javax.imageio.ImageIO.write(image, "png", output);
        return output.toByteArray();
    }
}
