package eu.royalblackwater.api.warehouse;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.WarehousePortCreate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import eu.royalblackwater.api.warehouse.service.WarehousePortService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
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

class WarehousePortServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ADMIN = new AuthenticatedUser(7, "admin", "admin", true, true, true);
    private static final AuthenticatedUser MEMBER = new AuthenticatedUser(8, "member", "user", false, false, false);

    @Test
    void authenticatedMembersReceiveOnlyActiveCatalogPorts() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.query(WarehouseQueries.ACTIVE_PORTS_SELECT_01, Map.of()))
                .thenReturn(List.of(row(1, "Tortuga", true)));
        when(repository.optional(eq(WarehouseQueries.ACTIVE_PORT_BY_NAME_SELECT_01), anyMap()))
                .thenReturn(Optional.of(Map.of("id", 1L, "name", "Tortuga")));

        List<?> ports = service(repository).active(MEMBER);

        assertThat(ports).hasSize(1);
        assertThat(service(repository).requireActiveName(" tortuga ")).isEqualTo("Tortuga");
    }

    @Test
    void administratorsCreateManagedPorts() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.count(eq(WarehouseQueries.PORT_NAME_EXISTS_SELECT_01), anyMap())).thenReturn(0L);
        when(repository.insertReturningId(eq(WarehouseQueries.CREATE_PORT_INSERT_01), anyMap())).thenReturn(42L);
        when(repository.optional(WarehouseQueries.PORT_SELECT_01, Map.of("id", 42L)))
                .thenReturn(Optional.of(row(42, "New Haven", true)));

        var created = service(repository).create(new WarehousePortCreate(" New Haven ", 420L, true), ADMIN);

        assertThat(created.name()).isEqualTo("New Haven");
    }

    @Test
    void membersCannotManagePortCatalog() {
        assertThatThrownBy(() -> service(mock(WarehouseRepository.class))
                .create(new WarehousePortCreate("New Haven", 420L, true), MEMBER))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("administrator access");
    }

    @Test
    void unknownOrInactivePortNamesAreRejectedForStockEntries() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.optional(eq(WarehouseQueries.ACTIVE_PORT_BY_NAME_SELECT_01), anyMap()))
                .thenReturn(Optional.empty());

        assertThatThrownBy(() -> service(repository).requireActiveName("Nassau"))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("active warehouse port");
    }

    private static WarehousePortService service(WarehouseRepository repository) {
        return new WarehousePortService(repository, mock(AuditService.class), CLOCK);
    }

    private static Map<String, Object> row(long id, String name, boolean active) {
        LocalDateTime timestamp = LocalDateTime.of(2030, 1, 15, 12, 0);
        return Map.of("id", id, "name", name, "sort_order", 100L, "is_active", active,
                "created_at", timestamp, "updated_at", timestamp);
    }
}
