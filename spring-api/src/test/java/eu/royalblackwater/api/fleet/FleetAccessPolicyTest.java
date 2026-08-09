package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.dto.FleetMembershipManagementRead;
import eu.royalblackwater.api.dto.FleetMembershipUpdate;
import eu.royalblackwater.api.fleet.dto.FleetMembershipTargetDto;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.fleet.repository.FleetDataRepository;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class FleetAccessPolicyTest {
    @Test
    void staffCanManageEveryFleetWithoutDependingOnMembershipRows() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        FleetAccessPolicy policy = new FleetAccessPolicy(repository);
        AuthenticatedUser administrator = new AuthenticatedUser(1, "admin", "admin", true, true, true);

        assertThat(policy.canManageFleet(administrator, 42L)).isTrue();
        assertThat(policy.managedFleetIds(administrator, List.of(42L, 43L))).containsExactlyInAnyOrder(42L, 43L);
        verifyNoInteractions(repository);
    }


    @Test
    void lastBootstrapAdmiralDoesNotLoadAssignableRolesForReadOnlyManagementMetadata() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        FleetAccessPolicy policy = new FleetAccessPolicy(repository);
        AuthenticatedUser administrator = new AuthenticatedUser(1, "admin", "admin", true, true, true);
        FleetMembershipTargetDto lastAdmiral = new FleetMembershipTargetDto(
                1L, "fleet_admiral", 80L, "active", "admin");

        FleetMembershipManagementRead permissions = policy.permissions(administrator, 42L, lastAdmiral);

        assertThat(permissions.canEditDirectory()).isTrue();
        assertThat(permissions.canChangeRole()).isFalse();
        assertThat(permissions.canChangeStatus()).isFalse();
        assertThat(permissions.assignableRoles()).isEmpty();
        assertThat(permissions.reason()).isEqualTo("last_admiral");
        verify(repository, never()).query(anyString(), anyMap());
    }

    @Test
    void protectsTheLastActiveFleetAdmiralFromDemotionAndDeactivation() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of(
                Map.of("code", "member"), Map.of("code", "fleet_lieutenant")));
        FleetAccessPolicy policy = new FleetAccessPolicy(repository);
        AuthenticatedUser administrator = new AuthenticatedUser(1, "admin", "admin", true, true, true);
        FleetMembershipTargetDto lastAdmiral = new FleetMembershipTargetDto(
                1L, "fleet_admiral", 80L, "active", "admin");

        assertThatThrownBy(() -> policy.validateMembershipUpdate(administrator, 42L, lastAdmiral,
                new FleetMembershipUpdate(null, null, null, "member", null)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("last active fleet admiral");
        assertThatThrownBy(() -> policy.validateMembershipUpdate(administrator, 42L, lastAdmiral,
                new FleetMembershipUpdate(null, null, null, null, "inactive")))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("last active fleet admiral");
    }

    @Test
    void onlyTheBootstrapAdministratorCanAssignFounder() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of(Map.of("code", "member")));
        FleetAccessPolicy policy = new FleetAccessPolicy(repository);
        AuthenticatedUser administrator = new AuthenticatedUser(1, "admin", "admin", true, true, false);
        FleetMembershipTargetDto member = new FleetMembershipTargetDto(
                2L, "member", 10L, "active", "user");

        assertThatThrownBy(() -> policy.validateMembershipUpdate(administrator, 42L, member,
                new FleetMembershipUpdate(null, null, null, "founder", null)))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("bootstrap administrator");
    }

    @Test
    void bootstrapAdministratorSeesFounderAsAssignable() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of(Map.of("code", "member")));
        FleetAccessPolicy policy = new FleetAccessPolicy(repository);
        AuthenticatedUser bootstrap = new AuthenticatedUser(1, "admin", "admin", true, true, true);
        FleetMembershipTargetDto member = new FleetMembershipTargetDto(
                2L, "member", 10L, "active", "user");

        assertThat(policy.permissions(bootstrap, 42L, member).assignableRoles())
                .contains("founder");
    }

    @Test
    void nonBootstrapAdministratorsCannotModifyFounderMemberships() {
        FleetDataRepository repository = mock(FleetDataRepository.class);
        FleetAccessPolicy policy = new FleetAccessPolicy(repository);
        AuthenticatedUser administrator = new AuthenticatedUser(1, "admin", "admin", true, true, false);
        FleetMembershipTargetDto founder = new FleetMembershipTargetDto(
                2L, "founder", 90L, "active", "user");

        assertThat(policy.permissions(administrator, 42L, founder).reason()).isEqualTo("founder");
    }
}
