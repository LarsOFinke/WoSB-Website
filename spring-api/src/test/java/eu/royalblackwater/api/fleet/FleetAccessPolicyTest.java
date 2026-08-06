package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.dto.FleetMembershipUpdate;
import eu.royalblackwater.api.fleet.dto.FleetMembershipTargetDto;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.fleet.repository.FleetDataRepository;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
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
}
