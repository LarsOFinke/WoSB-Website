package eu.royalblackwater.api.warehouse;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.WarehouseEntryCreate;
import eu.royalblackwater.api.dto.WarehouseEntryUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import eu.royalblackwater.api.warehouse.service.WarehouseService;
import eu.royalblackwater.api.warehouse.service.WarehousePortService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class WarehouseServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ADMIN =
            new AuthenticatedUser(7, "lars", "admin", true, true, true);
    private static final AuthenticatedUser MODERATOR =
            new AuthenticatedUser(9, "quartermaster", "moderator", true, false, false);
    private static final AuthenticatedUser MEMBER =
            new AuthenticatedUser(8, "member", "user", false, false, false);

    @Test
    void staffCreatesCustomHolderStockAndRecordsFleetScopedAudit() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        AuditService audit = mock(AuditService.class);
        when(repository.optional(eq(WarehouseQueries.FLEET_SELECT_01), anyMap()))
                .thenReturn(Optional.of(Map.of("id", 2L, "name", "Blackwater")));
        when(repository.insertReturningId(eq(WarehouseQueries.CREATE_INSERT_01), anyMap())).thenReturn(41L);
        when(repository.optional(anyString(), eq(Map.of("id", 41L))))
                .thenReturn(Optional.of(row(41, 1, 650, true)));

        var created = service(repository, audit).create(
                new WarehouseEntryCreate(650, "Blackwater", 2, null, "Nassau", true, "Iron"), MODERATOR);

        assertThat(created.holderName()).isEqualTo("Blackwater");
        assertThat(created.reserved()).isTrue();
        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).insertReturningId(eq(WarehouseQueries.CREATE_INSERT_01), parameters.capture());
        assertThat(parameters.getValue()).containsEntry("customHolderName", "Blackwater")
                .containsEntry("memberUserId", null);
        verify(audit).record(eq(MODERATOR), eq("warehouse_entry"), eq(41L), eq("create"),
                anyString(), eq(List.of("fleet_id", "holder", "port", "resource", "amount", "reserved")),
                eq("fleet"), eq(2L));
    }

    @Test
    void rejectsMemberLinksOutsideTheSelectedFleet() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.optional(eq(WarehouseQueries.FLEET_SELECT_01), anyMap()))
                .thenReturn(Optional.of(Map.of("id", 2L, "name", "Blackwater")));
        when(repository.optional(eq(WarehouseQueries.MEMBER_SELECT_01), anyMap())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service(repository, mock(AuditService.class)).create(
                new WarehouseEntryCreate(10, null, 2, 99L, "Nassau", false, "Iron"), ADMIN))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("not an active member");
    }

    @Test
    void reservationOnlyUpdateUsesTheDedicatedWebhookAuditAction() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        AuditService audit = mock(AuditService.class);
        Map<String, Object> before = row(41, 1, 650, false);
        Map<String, Object> after = row(41, 2, 650, true);
        when(repository.optional(anyString(), eq(Map.of("id", 41L))))
                .thenReturn(Optional.of(before), Optional.of(after));
        when(repository.optional(eq(WarehouseQueries.FLEET_SELECT_01), anyMap()))
                .thenReturn(Optional.of(Map.of("id", 2L, "name", "Blackwater")));
        when(repository.update(eq(WarehouseQueries.UPDATE_UPDATE_01), anyMap())).thenReturn(1);

        var updated = service(repository, audit).update(41,
                new WarehouseEntryUpdate(650, "Blackwater", 2, null, "Nassau", true, "Iron", 1), ADMIN);

        assertThat(updated.version()).isEqualTo(2);
        verify(audit).record(eq(ADMIN), eq("warehouse_entry"), eq(41L), eq("reservation"),
                anyString(), eq(List.of("reserved")), eq("fleet"), eq(2L));
    }

    @Test
    void staleUpdateFailsWithConflict() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.optional(anyString(), eq(Map.of("id", 41L))))
                .thenReturn(Optional.of(row(41, 2, 650, false)));
        when(repository.optional(eq(WarehouseQueries.FLEET_SELECT_01), anyMap()))
                .thenReturn(Optional.of(Map.of("id", 2L, "name", "Blackwater")));
        when(repository.update(eq(WarehouseQueries.UPDATE_UPDATE_01), anyMap())).thenReturn(0);

        assertThatThrownBy(() -> service(repository, mock(AuditService.class)).update(41,
                new WarehouseEntryUpdate(900, "Blackwater", 2, null, "Nassau", false, "Iron", 1), ADMIN))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(409));
    }

    @Test
    void authenticatedMembersCanReadWarehouse() {
        WarehouseRepository repository = mock(WarehouseRepository.class);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of());
        when(repository.required(anyString(), anyMap())).thenReturn(Map.of(
                "available_stock", 0L, "matching_stock", 0L, "reserved_stock", 0L, "total", 0L));

        var page = service(repository, mock(AuditService.class))
                .list(MEMBER, null, null, null, null, null, 100, 0);

        assertThat(page.total()).isZero();
        assertThat(page.items()).isEmpty();
    }

    @Test
    void serviceBoundaryRejectsMemberMutations() {
        assertThatThrownBy(() -> service(mock(WarehouseRepository.class), mock(AuditService.class))
                .create(new WarehouseEntryCreate(10, "Blackwater", 2, null, "Nassau", false, "Iron"), MEMBER))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("require staff access");
    }

    private static WarehouseService service(WarehouseRepository repository, AuditService audit) {
        WarehousePortService ports = mock(WarehousePortService.class);
        when(ports.requireActiveName(anyString())).thenAnswer(invocation -> invocation.getArgument(0));
        return new WarehouseService(repository, ports, audit, CLOCK);
    }

    private static Map<String, Object> row(long id, long version, long amount, boolean reserved) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", id);
        row.put("fleet_id", 2L);
        row.put("fleet_name", "Royal Blackwater Fleet");
        row.put("member_user_id", null);
        row.put("custom_holder_name", "Blackwater");
        row.put("holder_name", "Blackwater");
        row.put("port", "Nassau");
        row.put("resource", "Iron");
        row.put("amount", amount);
        row.put("reserved", reserved);
        row.put("version", version);
        row.put("created_at", LocalDateTime.of(2030, 1, 1, 12, 0));
        row.put("updated_at", LocalDateTime.of(2030, 1, 15, 12, 0));
        row.put("updated_by", "Lars");
        return row;
    }
}
