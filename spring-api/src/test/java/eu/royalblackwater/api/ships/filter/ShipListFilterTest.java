package eu.royalblackwater.api.ships.filter;

import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ShipListFilterTest {
    @Test
    void normalizesOptionalFiltersAndPagination() {
        ShipListFilter filter = ShipListFilter.from("  Frigate  ", 5L, "  Heavy  ", 25, 50);
        assertThat(filter.page().search()).isEqualTo("Frigate");
        assertThat(filter.page().limit()).isEqualTo(25);
        assertThat(filter.page().offset()).isEqualTo(50);
        assertThat(filter.rate()).isEqualTo(5L);
        assertThat(filter.shipType()).isEqualTo("Heavy");
    }

    @Test
    void allUsesSafeDefaults() {
        ShipListFilter filter = ShipListFilter.all();
        assertThat(filter.page().limit()).isEqualTo(250);
        assertThat(filter.page().offset()).isZero();
        assertThat(filter.rate()).isNull();
        assertThat(filter.shipType()).isNull();
    }

    @Test
    void rateMustRemainWithinSupportedRange() {
        assertThatThrownBy(() -> ShipListFilter.from(null, 8L, null, 20, 0))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("rate must be between 1 and 7");
    }
}
