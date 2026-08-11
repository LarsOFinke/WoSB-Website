package eu.royalblackwater.api.files;

import java.lang.reflect.Method;
import eu.royalblackwater.api.config.StorageProperties;
import eu.royalblackwater.api.files.repository.FileAssetRepository;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.files.service.ImageAssetOptimizer;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

class FileAssetServiceBehaviorTest {
    private final FileAssetRepository repository = mock(FileAssetRepository.class);
    private final FileAssetService service = new FileAssetService(repository,
            new StorageProperties(Path.of("/tmp/rbf-file-test"), 12, 24, 50, 250, 4096, 1),
            new ImageAssetOptimizer(),
            Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC));

    @Test
    void rejectsUnsupportedContextsBeforeQueryingOrWritingStorage() {
        assertThatThrownBy(() -> service.list(7, "avatar"))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Unsupported upload usage context");
        verify(repository, never()).query(org.mockito.ArgumentMatchers.anyString(), org.mockito.ArgumentMatchers.anyMap());
    }

    @Test
    void rejectsEmptyUploadsBeforeQuotaOrFilesystemWork() {
        MultipartFile upload = mock(MultipartFile.class);
        org.mockito.Mockito.when(upload.isEmpty()).thenReturn(true);
        AuthenticatedUser owner = new AuthenticatedUser(7, "captain", "user", false, false, false);

        assertThatThrownBy(() -> service.upload(upload, "general", owner))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Empty files cannot be uploaded");
    }

    @Test
    void rejectsUnknownAttachmentRelationsAndNormalizesEmptyOwnedFileSelections() {
        assertThatThrownBy(() -> service.attach("users", "id", 1L, List.of(), "general"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Unsupported attachment relation");
        AuthenticatedUser owner = new AuthenticatedUser(7, "captain", "user", false, false, false);
        org.assertj.core.api.Assertions.assertThat(service.ownedFiles(List.of(), owner)).isEmpty();
    }
    @Test
    void transactionCleanupHooksDeleteFilesAtTheCorrectTransactionPhase() throws Exception {
        Path rollbackFile = Files.createTempFile("rbf-rollback-cleanup", ".tmp");
        TransactionSynchronizationManager.initSynchronization();
        try {
            invokeCleanupHook("registerRollbackCleanup", rollbackFile);
            var synchronizations = TransactionSynchronizationManager.getSynchronizations();
            assertThat(synchronizations).hasSize(1);
            synchronizations.getFirst().afterCompletion(TransactionSynchronization.STATUS_ROLLED_BACK);
            assertThat(rollbackFile).doesNotExist();
        } finally {
            TransactionSynchronizationManager.clearSynchronization();
            Files.deleteIfExists(rollbackFile);
        }

        Path commitFile = Files.createTempFile("rbf-commit-cleanup", ".tmp");
        TransactionSynchronizationManager.initSynchronization();
        try {
            invokeCleanupHook("registerCommitCleanup", commitFile);
            var synchronizations = TransactionSynchronizationManager.getSynchronizations();
            assertThat(synchronizations).hasSize(1);
            synchronizations.getFirst().afterCommit();
            assertThat(commitFile).doesNotExist();
        } finally {
            TransactionSynchronizationManager.clearSynchronization();
            Files.deleteIfExists(commitFile);
        }
    }

    private static void invokeCleanupHook(String name, Path path) throws Exception {
        Method method = FileAssetService.class.getDeclaredMethod(name, Path.class);
        method.setAccessible(true);
        method.invoke(null, path);
    }

}
