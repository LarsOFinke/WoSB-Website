package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.builds.service.BuildStatCalculator;
import eu.royalblackwater.api.dto.BuildStatRow;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class BuildStatCalculatorTest {
    private final BuildStatCalculator calculator = new BuildStatCalculator();

    @Test
    void stacksPercentagesMultiplicativelyAndAddsFlatEffectsAfterwards() {
        List<BuildStatRow> rows = calculator.calculate(
                Map.of("speed_min_knots", 7.6, "speed_knots", 10.6, "armor", 5.5, "maneuverability", 72),
                Map.of("speed_pct", 9, "speed_knots", 4.1, "armor_pct", -10, "turn_rate_pct", 5),
                List.of(Map.of("speed_pct", 5, "armor_pct", 5),
                        Map.of("speed_pct", 4, "armor_pct", -15, "turn_rate_pct", 5),
                        Map.of("speed_knots", 4.1)));
        assertThat(value(rows, "speed_min_knots").effective()).isEqualTo(8.3);
        assertThat(value(rows, "speed_knots").effective()).isEqualTo(15.4);
        assertThat(value(rows, "armor").effective()).isEqualTo(4.9);
        assertThat(value(rows, "maneuverability").effective()).isEqualTo(76L);
    }

    @Test
    void usesDecimalHalfUpForWholeCrewCapacity() {
        BuildStatRow row = value(calculator.calculate(
                Map.of("crew_capacity", 10), Map.of("crew_capacity_pct", 5),
                List.of(Map.of("crew_capacity_pct", 5))), "crew_capacity");
        assertThat(row.effective()).isEqualTo(11L);
    }

    private static BuildStatRow value(List<BuildStatRow> rows, String key) {
        return rows.stream().filter(row -> row.key().equals(key)).findFirst().orElseThrow();
    }
}
