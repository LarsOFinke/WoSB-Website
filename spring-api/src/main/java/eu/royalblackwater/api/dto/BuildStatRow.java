// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record BuildStatRow(
        Number base,
        @NotNull String category,
        String effectKey,
        Number effective,
        Number flatModifier,
        Boolean isDebuff,
        @NotNull String key,
        @NotNull String label,
        Number modifier,
        String modifierKind,
        Number percentModifier,
        Long precision,
        String source,
        String unit) { }
