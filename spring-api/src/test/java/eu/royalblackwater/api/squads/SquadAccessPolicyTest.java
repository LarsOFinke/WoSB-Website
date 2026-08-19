package eu.royalblackwater.api.squads;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.squads.service.SquadAccessPolicy;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class SquadAccessPolicyTest {
    private static final AuthenticatedUser MEMBER =
            new AuthenticatedUser(7, "member", "user", false, false, false);
    private static final AuthenticatedUser MODERATOR =
            new AuthenticatedUser(8, "moderator", "moderator", true, false, false);

    @Test
    void staffCanManageAndAdministerSquads() {
        SquadAccessPolicy policy = new SquadAccessPolicy();

        assertThat(policy.canManage(MODERATOR, 13L, 11L)).isTrue();
        assertThat(policy.canAdminister(MODERATOR, 13L, 11L)).isTrue();
    }

    @Test
    void legacySquadOrFleetLeadershipCannotBypassTheStaffThreshold() {
        SquadAccessPolicy policy = new SquadAccessPolicy();

        assertThat(policy.canManage(MEMBER, 13L, 11L)).isFalse();
        assertThat(policy.canAdminister(MEMBER, 13L, 11L)).isFalse();
    }
}
