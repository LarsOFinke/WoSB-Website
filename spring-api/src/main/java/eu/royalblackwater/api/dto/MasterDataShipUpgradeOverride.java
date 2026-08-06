// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import java.util.Map;

public record MasterDataShipUpgradeOverride(
        @Min(1) long optionId,
        Map<String, Double> statEffects) { }
