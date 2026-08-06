package eu.royalblackwater.api.squads;

import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.squads.repository.SquadRepository;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.squads.service.SquadAccessPolicy;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class SquadAccessPolicyTest {
    private static final AuthenticatedUser MEMBER =
            new AuthenticatedUser(7, "member", "user", false, false, false);

    @Test
    void fleetManagementCapabilityGrantsSquadManagementAndAdministration() {
        SquadRepository repository = mock(SquadRepository.class);
        FleetAccessPolicy fleets = mock(FleetAccessPolicy.class);
        when(fleets.canManageFleet(MEMBER, 11L)).thenReturn(true);
        SquadAccessPolicy policy = new SquadAccessPolicy(repository, fleets);

        assertThat(policy.canManage(MEMBER, 13L, 11L)).isTrue();
        assertThat(policy.canAdminister(MEMBER, 13L, 11L)).isTrue();
    }

    @Test
    void squadOfficersManageRosterButOnlyLeadersAdministerCommandRoles() {
        SquadRepository repository = mock(SquadRepository.class);
        FleetAccessPolicy fleets = mock(FleetAccessPolicy.class);
        when(fleets.canManageFleet(MEMBER, 11L)).thenReturn(false);
        when(repository.optional(anyString(), anyMap()))
                .thenReturn(Optional.of(Map.of("code", "officer")))
                .thenReturn(Optional.of(Map.of("code", "officer")))
                .thenReturn(Optional.of(Map.of("code", "leader")));
        SquadAccessPolicy policy = new SquadAccessPolicy(repository, fleets);

        assertThat(policy.canManage(MEMBER, 13L, 11L)).isTrue();
        assertThat(policy.canAdminister(MEMBER, 13L, 11L)).isFalse();
        assertThat(policy.canAdminister(MEMBER, 13L, 11L)).isTrue();
    }
}
