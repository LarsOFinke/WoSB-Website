package eu.royalblackwater.api.operations;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.BackupControlStatus;
import eu.royalblackwater.api.dto.BackupDiscoveryRequest;
import eu.royalblackwater.api.dto.DatabaseRestoreRequest;
import eu.royalblackwater.api.operations.mapper.OperationsDtoMapper;
import eu.royalblackwater.api.operations.repository.ControlFileStore;
import eu.royalblackwater.api.operations.service.BackupControlService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class BackupControlServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);

    @Test
    void rejectsLocalBackupHostsBeforePublishingControlRequests() {
        BackupControlService service = service(mock(ControlFileStore.class), mock(OperationsDtoMapper.class));
        AuthenticatedUser actor = new AuthenticatedUser(7, "captain", "admin", true, true, true);

        assertThatThrownBy(() -> service.discover(actor, new BackupDiscoveryRequest("localhost", 22L), "a".repeat(32)))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Invalid public backup host");
    }

    @Test
    void restoreOperationsRequireTheBootstrapAdministratorBeforeTokenValidation() {
        BackupControlService service = service(mock(ControlFileStore.class), mock(OperationsDtoMapper.class));
        AuthenticatedUser regularAdmin = new AuthenticatedUser(7, "admin", "admin", true, true, false);

        assertThatThrownBy(() -> service.restoreDatabase(regularAdmin,
                new DatabaseRestoreRequest("short", "0".repeat(64), "RESTORE DATABASE")))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(403))
                .hasMessageContaining("Bootstrap administrator required");
    }

    @Test
    void staleRunningStatusIsFailedClosedWhenTheHostHeartbeatDisappears() {
        ControlFileStore files = mock(ControlFileStore.class);
        OperationsDtoMapper mapper = mock(OperationsDtoMapper.class);
        BackupControlStatus expected = mock(BackupControlStatus.class);
        when(files.readStatus("backup-status.json")).thenReturn(Map.of(
                "state", "running",
                "started_at", "2030-01-15T11:00:00Z"));
        when(files.readRequest("backup.request")).thenReturn(Map.of());
        when(files.requestExists("backup.request")).thenReturn(false);
        when(mapper.backupStatus(anyMap())).thenReturn(expected);
        BackupControlService service = service(files, mapper);

        assertThat(service.status()).isSameAs(expected);
        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> payload = ArgumentCaptor.forClass(Map.class);
        org.mockito.Mockito.verify(mapper).backupStatus(payload.capture());
        assertThat(payload.getValue()).containsEntry("state", "failed");
        assertThat(String.valueOf(payload.getValue().get("message"))).contains("stopped reporting");
    }

    private static BackupControlService service(ControlFileStore files, OperationsDtoMapper mapper) {
        return new BackupControlService(files, mapper, new ObjectMapper(), mock(AuditService.class), CLOCK);
    }
}
