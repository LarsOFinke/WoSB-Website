package eu.royalblackwater.api.transport;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.Set;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

class ListFilterTest {
    @Test
    void normalizesAndBoundsListParameters() {
        ListFilter filter = ListFilter.from(Map.of("search", "  Nelson  ", "limit", 25, "offset", 50), 20, 100);
        assertThat(filter).isEqualTo(new ListFilter("Nelson", 25, 50));
    }

    @Test
    void usesDefaultsForMissingValues() {
        assertThat(ListFilter.from(Map.of(), 20, 100)).isEqualTo(new ListFilter(null, 20, 0));
    }

    @Test
    void rejectsOverflowBeforeNarrowingToInt() {
        assertThatThrownBy(() -> ListFilter.from(Map.of("limit", new BigInteger("4294967297")), 20, 100))
                .isInstanceOf(ResponseStatusException.class);
    }

    @Test
    void validatesEnumAndPositiveLongFilters() {
        assertThat(ListFilter.optionalEnum(Map.of("status", " ACTIVE "), "status", Set.of("active", "inactive")))
                .isEqualTo("active");
        assertThat(ListFilter.optionalPositiveLong(Map.of("fleet_id", 42L), "fleet_id")).isEqualTo(42L);
        assertThatThrownBy(() -> ListFilter.optionalEnum(
                Map.of("status", "unknown"), "status", Set.of("active", "inactive")))
                .isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> ListFilter.optionalPositiveLong(
                Map.of("fleet_id", new BigInteger("18446744073709551617")), "fleet_id"))
                .isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> ListFilter.from(Map.of("limit", new BigDecimal("1.5")), 20, 100))
                .isInstanceOf(ResponseStatusException.class);
    }

    @Test
    void rejectsUnboundedOffsetsAndSearchTerms() {
        assertThatThrownBy(() -> ListFilter.from(Map.of("offset", 100_001), 20, 100))
                .isInstanceOf(ResponseStatusException.class);
        assertThatThrownBy(() -> ListFilter.from(Map.of("search", "x".repeat(121)), 20, 100))
                .isInstanceOf(ResponseStatusException.class);
    }
}
