package eu.royalblackwater.api.operations;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.operations.mapper.OperationsDtoMapper;
import eu.royalblackwater.api.operations.repository.ControlFileStore;
import eu.royalblackwater.api.operations.service.SystemUpdateService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class SystemUpdateServiceTest {
    private static final Instant NOW = Instant.parse("2030-01-15T12:00:00Z");
    private static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);
    private static final AuthenticatedUser ADMIN = new AuthenticatedUser(1, "admin", "admin", true, true, true);

    @Test
    void idleStatusDefaultsToUpdateAndAllowsNewRequest() {
        ControlFileStore files = mock(ControlFileStore.class);
        when(files.readStatus("update-status.json")).thenReturn(Map.of());
        when(files.readRequest("update.request")).thenReturn(Map.of());

        var status = service(files, mock(AuditService.class)).status();

        assertThat(status.state()).isEqualTo("idle");
        assertThat(status.operation()).isEqualTo("update");
        assertThat(status.requestAvailable()).isTrue();
        assertThat(status.message()).contains("No server operation");
    }

    @Test
    void staleRunningOperationFailsClosedAfterHeartbeatTimeout() {
        ControlFileStore files = mock(ControlFileStore.class);
        when(files.readStatus("update-status.json")).thenReturn(Map.of(
                "state", "running",
                "operation", "restart",
                "heartbeat_at", NOW.minusSeconds(181).toString()));
        when(files.readRequest("update.request")).thenReturn(Map.of());

        var status = service(files, mock(AuditService.class)).status();

        assertThat(status.state()).isEqualTo("failed");
        assertThat(status.finishedAt()).isEqualTo(NOW.toString());
        assertThat(status.message()).contains("failed");
    }

    @Test
    void orphanedRequestIsPresentedAsQueued() {
        ControlFileStore files = mock(ControlFileStore.class);
        when(files.readStatus("update-status.json")).thenReturn(Map.of("state", "succeeded"));
        when(files.readRequest("update.request")).thenReturn(Map.of(
                "operation", "rollback", "requested_at", "2030-01-15T11:59:00Z"));
        when(files.requestExists("update.request")).thenReturn(true);

        var status = service(files, mock(AuditService.class)).status();

        assertThat(status.state()).isEqualTo("queued");
        assertThat(status.operation()).isEqualTo("rollback");
        assertThat(status.requestAvailable()).isFalse();
    }

    @Test
    void requestValidatesOperationPublishesAtomicallyAndAuditsActor() {
        ControlFileStore files = mock(ControlFileStore.class);
        AuditService audit = mock(AuditService.class);
        when(files.readStatus("update-status.json")).thenReturn(Map.of());
        when(files.readRequest("update.request")).thenReturn(Map.of());
        when(files.requestExists("update.request")).thenReturn(false);

        var result = service(files, audit).request(ADMIN, " RESTART ");

        assertThat(result.accepted()).isTrue();
        verify(files).publishRequest(eq("update.request"), org.mockito.ArgumentMatchers.argThat(payload ->
                "restart".equals(payload.get("operation"))
                        && "admin".equals(payload.get("requested_by"))
                        && NOW.toString().equals(payload.get("requested_at"))));
        verify(audit).record(eq(ADMIN), eq("system_update"), eq("restart"), eq("request"), any(), any());
    }

    @Test
    void requestRejectsUnknownAndConcurrentOperations() {
        ControlFileStore files = mock(ControlFileStore.class);
        AuditService audit = mock(AuditService.class);
        SystemUpdateService service = service(files, audit);

        assertThatThrownBy(() -> service.request(ADMIN, "destroy"))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(400));

        when(files.readStatus("update-status.json")).thenReturn(Map.of("state", "running", "heartbeat_at", NOW.toString()));
        when(files.readRequest("update.request")).thenReturn(Map.of());
        when(files.requestExists("update.request")).thenReturn(true);
        assertThatThrownBy(() -> service.request(ADMIN, "update"))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(409));
    }

    private static SystemUpdateService service(ControlFileStore files, AuditService audit) {
        return new SystemUpdateService(files, audit, new OperationsDtoMapper(new ObjectMapper()), CLOCK);
    }
}
