package eu.royalblackwater.api.core.util;

import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;

/** Canonical conversion from an injected clock instant to persisted UTC time. */
public final class UtcDateTimes {
    private UtcDateTimes() { }

    public static LocalDateTime now(Clock clock) {
        if (clock == null) throw new IllegalArgumentException("Clock is required.");
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }
}
