// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

public record SecurityDayBucket(
        @NotNull LocalDate day,
        long loginFailures,
        long rateLimits,
        long reconnaissance,
        long totalEvents,
        long uniqueIps) { }
