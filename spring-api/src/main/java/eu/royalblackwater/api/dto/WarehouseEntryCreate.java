// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record WarehouseEntryCreate(
        @Min(0) @Max(999999999) long amount,
        String customHolderName,
        @Min(1) long fleetId,
        Long memberUserId,
        @NotNull @Size(min = 1, max = 120) String port,
        Boolean reserved,
        @NotNull @Size(min = 1, max = 120) String resource) { }
