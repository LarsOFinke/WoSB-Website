package eu.royalblackwater.api.squads;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.fleet.FleetAccessPolicy;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class SquadAccessPolicyTest {
    private static final AuthenticatedUser MEMBER =
            new AuthenticatedUser(7, "member", "user", false, false, false);

    @Test
    void fleetManagementCapabilityGrantsSquadManagementAndAdministration() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        FleetAccessPolicy fleets = mock(FleetAccessPolicy.class);
        when(fleets.canManageFleet(MEMBER, 11L)).thenReturn(true);
        SquadAccessPolicy policy = new SquadAccessPolicy(jdbc, fleets);

        assertThat(policy.canManage(MEMBER, 13L, 11L)).isTrue();
        assertThat(policy.canAdminister(MEMBER, 13L, 11L)).isTrue();
    }

    @Test
    void squadOfficersManageRosterButOnlyLeadersAdministerCommandRoles() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        FleetAccessPolicy fleets = mock(FleetAccessPolicy.class);
        when(fleets.canManageFleet(MEMBER, 11L)).thenReturn(false);
        when(jdbc.optional(anyString(), anyMap()))
                .thenReturn(Optional.of(Map.of("code", "officer")))
                .thenReturn(Optional.of(Map.of("code", "officer")))
                .thenReturn(Optional.of(Map.of("code", "leader")));
        SquadAccessPolicy policy = new SquadAccessPolicy(jdbc, fleets);

        assertThat(policy.canManage(MEMBER, 13L, 11L)).isTrue();
        assertThat(policy.canAdminister(MEMBER, 13L, 11L)).isFalse();
        assertThat(policy.canAdminister(MEMBER, 13L, 11L)).isTrue();
    }
}
