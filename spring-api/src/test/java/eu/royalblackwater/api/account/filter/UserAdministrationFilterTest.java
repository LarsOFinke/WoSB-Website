package eu.royalblackwater.api.account.filter;

import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class UserAdministrationFilterTest {
    @Test
    void normalizesRoleStatusFleetAndPagination() {
        UserAdministrationFilter filter = UserAdministrationFilter.from(
                "  Nelson  ", " MODERATOR ", " ACTIVE ", 7L, 25, 50);

        assertThat(filter.page().search()).isEqualTo("Nelson");
        assertThat(filter.page().limit()).isEqualTo(25);
        assertThat(filter.page().offset()).isEqualTo(50);
        assertThat(filter.role()).isEqualTo("moderator");
        assertThat(filter.status()).isEqualTo("active");
        assertThat(filter.fleetId()).isEqualTo(7L);
    }

    @Test
    void rejectsUnknownEnumsAndNonPositiveFleetIds() {
        assertThatThrownBy(() -> UserAdministrationFilter.from(null, "owner", null, null, 20, 0))
                .isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> UserAdministrationFilter.from(null, null, "pending", null, 20, 0))
                .isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> UserAdministrationFilter.from(null, null, null, 0L, 20, 0))
                .isInstanceOf(ResponseStatusException.class);
    }
}
