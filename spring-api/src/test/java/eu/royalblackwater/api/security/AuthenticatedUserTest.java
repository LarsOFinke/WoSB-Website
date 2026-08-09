package eu.royalblackwater.api.security;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class AuthenticatedUserTest {
    @Test
    void principalNameAdminGrantAndAuthorityFollowRoleContract() {
        AuthenticatedUser admin = new AuthenticatedUser(1, "captain", "admin", true, true, true);
        assertThat(admin.getName()).isEqualTo("captain");
        assertThat(admin.isAdmin()).isTrue();
        assertThat(admin.canGrantAdmin()).isTrue();
        assertThat(admin.authority()).isEqualTo("ROLE_ADMIN");

        AuthenticatedUser delegatedAdmin = new AuthenticatedUser(2, "officer", "admin", true, true, false);
        assertThat(delegatedAdmin.isAdmin()).isTrue();
        assertThat(delegatedAdmin.canGrantAdmin()).isFalse();

        AuthenticatedUser member = new AuthenticatedUser(3, "member", "user", false, false, false);
        assertThat(member.isAdmin()).isFalse();
        assertThat(member.canGrantAdmin()).isFalse();
        assertThat(member.authority()).isEqualTo("ROLE_USER");
    }
}
