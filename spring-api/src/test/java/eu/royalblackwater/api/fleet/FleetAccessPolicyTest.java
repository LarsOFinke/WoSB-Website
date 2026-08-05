package eu.royalblackwater.api.fleet;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.contract.FleetMembershipUpdate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

class FleetAccessPolicyTest {
    @Test
    void staffCanManageEveryFleetWithoutDependingOnMembershipRows() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        FleetAccessPolicy policy = new FleetAccessPolicy(jdbc);
        AuthenticatedUser administrator = new AuthenticatedUser(1, "admin", "admin", true, true, true);

        assertThat(policy.canManageFleet(administrator, 42L)).isTrue();
        assertThat(policy.managedFleetIds(administrator, List.of(42L, 43L))).containsExactlyInAnyOrder(42L, 43L);
        verifyNoInteractions(jdbc);
    }

    @Test
    void protectsTheLastActiveFleetAdmiralFromDemotionAndDeactivation() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        when(jdbc.count(anyString(), anyMap())).thenReturn(1L);
        when(jdbc.query(anyString(), anyMap())).thenReturn(List.of(
                Map.of("code", "member"), Map.of("code", "fleet_lieutenant")));
        FleetAccessPolicy policy = new FleetAccessPolicy(jdbc);
        AuthenticatedUser administrator = new AuthenticatedUser(1, "admin", "admin", true, true, true);
        Map<String, Object> lastAdmiral = Map.of(
                "user_id", 1L, "role", "fleet_admiral", "role_rank", 80L,
                "status", "active", "site_role", "admin");

        assertThatThrownBy(() -> policy.validateMembershipUpdate(administrator, 42L, lastAdmiral,
                new FleetMembershipUpdate(null, null, null, "member", null)))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("last active fleet admiral");
        assertThatThrownBy(() -> policy.validateMembershipUpdate(administrator, 42L, lastAdmiral,
                new FleetMembershipUpdate(null, null, null, null, "inactive")))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("last active fleet admiral");
    }
}
