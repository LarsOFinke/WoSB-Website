// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.util.Map;

public record MasterDataShipUpgradeOverrideRead(
        Map<String, Double> baseStatEffects,
        Map<String, Double> effectiveStatEffects,
        @Min(1) long optionId,
        @NotNull String optionName,
        Map<String, Double> statEffects) { }
