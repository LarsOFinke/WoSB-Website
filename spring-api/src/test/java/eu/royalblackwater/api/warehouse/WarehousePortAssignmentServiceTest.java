package eu.royalblackwater.api.warehouse;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.WarehousePortAssignmentUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import eu.royalblackwater.api.warehouse.service.WarehousePortAssignmentService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class WarehousePortAssignmentServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser MODERATOR = new AuthenticatedUser(7, "moderator", "moderator", true, false, false);
    private static final AuthenticatedUser MEMBER = new AuthenticatedUser(8, "member", "user", false, false, false);

    @Test
    void staffCanAssignAnActiveFleetMemberToAnActivePort() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.optional(WarehouseQueries.FLEET_SELECT_01, Map.of("fleetId", 4L)))
                .thenReturn(Optional.of(Map.of("id", 4L, "name", "Blackwater")));
        when(repository.count(eq(WarehouseQueries.ACTIVE_PORT_BY_ID_SELECT_01), anyMap())).thenReturn(1L);
        when(repository.count(eq(WarehouseQueries.ACTIVE_FLEET_MEMBER_SELECT_01), anyMap())).thenReturn(1L);
        when(repository.optional(eq(WarehouseQueries.ASSIGNMENT_SELECT_01), anyMap()))
                .thenReturn(Optional.of(row()));

        var result = service(repository).update(12L, new WarehousePortAssignmentUpdate(8L, 4L), MODERATOR);

        assertThat(result.assigneeUserId()).isEqualTo(8L);
        assertThat(result.portName()).isEqualTo("Nassau");
    }

    @Test
    void nonMemberCannotViewAnotherFleetsAssignments() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.optional(WarehouseQueries.FLEET_SELECT_01, Map.of("fleetId", 4L)))
                .thenReturn(Optional.of(Map.of("id", 4L, "name", "Blackwater")));
        when(repository.count(eq(WarehouseQueries.ACTIVE_FLEET_MEMBER_SELECT_01), anyMap())).thenReturn(0L);

        assertThatThrownBy(() -> service(repository).list(4L, MEMBER))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("not a member");
    }

    private static WarehousePortAssignmentService service(WarehouseRepository repository) {
        return new WarehousePortAssignmentService(repository, mock(AuditService.class), CLOCK);
    }

    private static Map<String, Object> row() {
        LocalDateTime timestamp = LocalDateTime.of(2030, 1, 15, 12, 0);
        return Map.of("fleet_id", 4L, "fleet_name", "Blackwater", "port_id", 12L,
                "port_name", "Nassau", "assignee_user_id", 8L, "assignee_name", "Member",
                "updated_at", timestamp);
    }
}
