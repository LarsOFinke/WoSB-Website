package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.FleetCreate;
import eu.royalblackwater.api.dto.FleetJoinRequest;
import eu.royalblackwater.api.dto.FleetRoleUpdate;
import eu.royalblackwater.api.fleet.mapper.FleetDtoMapper;
import eu.royalblackwater.api.fleet.repository.FleetDataRepository;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.fleet.service.FleetCommandService;
import eu.royalblackwater.api.fleet.service.FleetRoleService;
import eu.royalblackwater.api.fleet.service.FleetViewService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class FleetServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ACTOR =
            new AuthenticatedUser(7, "captain", "admin", true, true, true);

    @Test
    void commandServicePreventsCreatingASecondOfficialFleet() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        FleetCommandService service = command(repository);
        FleetCreate payload = mock(FleetCreate.class);

        assertThatThrownBy(() -> service.create(payload, ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("official fleet is already configured");
        verify(repository, never()).insertReturningId(anyString(), anyMap());
    }

    @Test
    void commandServiceRejectsJoiningAnyFleetOtherThanTheOfficialFleet() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of("id", 11L)));
        FleetCommandService service = command(repository);

        assertThatThrownBy(() -> service.join(new FleetJoinRequest(12L, null), ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Only the official fleet can be joined");
    }

    @Test
    void roleServiceRequiresExistingFleetsAndProtectsSystemRoles() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        FleetAccessPolicy policy = mock(FleetAccessPolicy.class);
        FleetRoleService service = new FleetRoleService(repository, policy, mock(AuditService.class), CLOCK,
                mock(FleetDtoMapper.class));

        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        assertThatThrownBy(() -> service.list(99L, false, ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Fleet not found");

        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of(
                "id", 5L, "is_system", true, "member_count", 0L,
                "can_manage_fleet", false, "can_manage_members", false)));
        assertThatThrownBy(() -> service.update(11L, 5L,
                new FleetRoleUpdate(null, null, true, null, "System", 20L), ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("System fleet roles cannot be changed");
    }

    @Test
    void viewServiceRejectsUnauthorizedManagementAndMissingMemberships() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        FleetAccessPolicy policy = mock(FleetAccessPolicy.class);
        FleetViewService service = new FleetViewService(repository, policy, mock(FleetDtoMapper.class));
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of("id", 11L)));
        when(policy.canManageFleet(ACTOR, 11L)).thenReturn(false);

        assertThatThrownBy(() -> service.manageable(ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(403));

        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.membership(77L, ACTOR))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("Membership not found");
    }

    private static FleetCommandService command(FleetDataRepository repository) {
        FleetViewService views = mock(FleetViewService.class);
        FleetAccessPolicy policy = mock(FleetAccessPolicy.class);
        return new FleetCommandService(repository, views, policy, mock(AuditService.class), CLOCK,
                mock(FleetDtoMapper.class));
    }
}
