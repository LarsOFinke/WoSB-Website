// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public record StatEffectDefinitionRead(
        @NotNull String category,
        @NotNull String key,
        @NotNull String label,
        @Min(0) @Max(6) long precision,
        @NotNull String translationKey,
        String unit,
        @NotNull String valueType) { }
