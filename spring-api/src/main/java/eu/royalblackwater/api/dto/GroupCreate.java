// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record GroupCreate(
        String activityPlan,
        Boolean allowGuests,
        String contactNote,
        String description,
        String expectations,
        String fleetRestriction,
        @Size(max = 80) String focus,
        @Min(2) @Max(50) Long maxMembers,
        Long maxShipRate,
        Long minShipRate,
        LocalDateTime scheduledEndAt,
        LocalDateTime scheduledStartAt,
        @NotNull @Size(min = 1, max = 140) String title) { }
