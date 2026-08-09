package eu.royalblackwater.api.squads.filter;

import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SquadListFilterTest {
    @Test
    void regularFilterNormalizesSearchFleetAndFlags() {
        SquadListFilter filter = SquadListFilter.from("  Alpha  ", 12L, true, 30, 60);

        assertThat(filter.page().search()).isEqualTo("Alpha");
        assertThat(filter.page().limit()).isEqualTo(30);
        assertThat(filter.page().offset()).isEqualTo(60);
        assertThat(filter.fleetId()).isEqualTo(12L);
        assertThat(filter.includeInactive()).isTrue();
        assertThat(filter.mineOnly()).isFalse();
    }

    @Test
    void mineFilterUsesBoundedDefaultsAndNoFleetConstraint() {
        SquadListFilter filter = SquadListFilter.mine();
        assertThat(filter.page().search()).isNull();
        assertThat(filter.page().limit()).isEqualTo(250);
        assertThat(filter.page().offset()).isZero();
        assertThat(filter.fleetId()).isNull();
        assertThat(filter.includeInactive()).isFalse();
        assertThat(filter.mineOnly()).isTrue();
    }

    @Test
    void rejectsInvalidFleetId() {
        assertThatThrownBy(() -> SquadListFilter.from(null, -1L, false, 20, 0))
                .isInstanceOf(ResponseStatusException.class);
    }
}
