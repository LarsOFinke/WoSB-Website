// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.List;

public record SecurityIpRow(
        @NotNull String clientIp,
        long eventCount,
        @NotNull LocalDate firstSeen,
        @NotNull LocalDate lastSeen,
        long loginFailurePoints,
        long loginFailures,
        long rateLimitPoints,
        long rateLimits,
        List<SecurityReasonBreakdown> reasons,
        long reconnaissance,
        long reconnaissancePoints,
        @NotNull String threatLevel,
        @Min(0) @Max(100) long threatScore,
        long volumeBonus) { }
