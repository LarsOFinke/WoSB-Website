// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record FleetCreate(
        String description,
        @NotNull @Size(min = 2, max = 80) String focus,
        Boolean isActive,
        @NotNull @Size(min = 2, max = 120) String name,
        @NotNull @Size(min = 2, max = 120) String slug,
        @Min(0) @Max(9999) Long sortOrder,
        String standingOrders) { }
