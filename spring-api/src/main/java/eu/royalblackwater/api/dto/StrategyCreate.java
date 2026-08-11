// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record StrategyCreate(
        @NotNull @Size(min = 1, max = 180) String title,
        String description,
        @Min(1) long backgroundFileId,
        @NotNull @Size(min = 1, max = 200000) String overlayJson) { }
