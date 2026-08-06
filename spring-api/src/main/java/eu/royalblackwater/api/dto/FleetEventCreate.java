// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;

public record FleetEventCreate(
        Boolean allDay,
        @Size(max = 80) String category,
        String description,
        @NotNull LocalDateTime endAt,
        String location,
        @Size(max = 20) List<RaidHelperDispatchSelection> raidHelperDispatches,
        Boolean raidHelperEnabled,
        Long squadId,
        @NotNull LocalDateTime startAt,
        @NotNull @Size(min = 1, max = 160) String title) { }
