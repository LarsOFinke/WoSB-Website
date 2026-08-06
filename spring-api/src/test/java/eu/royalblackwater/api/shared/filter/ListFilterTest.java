package eu.royalblackwater.api.shared.filter;

import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ListFilterTest {
    @Test
    void normalizesAndBoundsListParameters() {
        ListFilter filter = ListFilter.of("  Nelson  ", 25, 50, 100);
        assertThat(filter).isEqualTo(new ListFilter("Nelson", 25, 50));
    }

    @Test
    void acceptsContractDefaults() {
        assertThat(ListFilter.of(null, 20, 0, 100))
                .isEqualTo(new ListFilter(null, 20, 0));
    }

    @Test
    void rejectsValuesOutsideTheBoundedIntegerRange() {
        assertThatThrownBy(() -> ListFilter.of(null, Long.MAX_VALUE, 0, 100))
                .isInstanceOf(ResponseStatusException.class);
    }

    @Test
    void validatesEnumAndPositiveLongFilters() {
        assertThat(ListFilter.optionalEnum(" ACTIVE ", "status", Set.of("active", "inactive")))
                .isEqualTo("active");
        assertThat(ListFilter.optionalPositiveLong(42L, "fleet_id")).isEqualTo(42L);
        assertThatThrownBy(() -> ListFilter.optionalEnum(
                "unknown", "status", Set.of("active", "inactive")))
                .isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> ListFilter.optionalPositiveLong(-1L, "fleet_id"))
                .isInstanceOf(ResponseStatusException.class);
    }

    @Test
    void rejectsUnboundedOffsetsAndSearchTerms() {
        assertThatThrownBy(() -> ListFilter.of(null, 20, 100_001, 100))
                .isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> ListFilter.of("x".repeat(121), 20, 0, 100))
                .isInstanceOf(ResponseStatusException.class);
    }
}
