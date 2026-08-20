// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record WarehousePortUpdate(
        @NotNull @Size(min = 1, max = 120) String name,
        @Min(0) @Max(100000) Long sortOrder,
        Boolean isActive) { }
