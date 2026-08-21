package eu.royalblackwater.api.core;

import eu.royalblackwater.api.core.util.UtcDateTimes;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class UtcDateTimesTest {
    @Test
    void convertsAnInjectedInstantToUtcWithoutUsingTheClockZone() {
        Clock clock = Clock.fixed(Instant.parse("2030-01-15T12:34:56Z"), ZoneOffset.ofHours(9));

        assertThat(UtcDateTimes.now(clock)).hasToString("2030-01-15T12:34:56");
    }

    @Test
    void rejectsMissingClock() {
        assertThatThrownBy(() -> UtcDateTimes.now(null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Clock is required.");
    }
}
