// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.util.List;
import java.util.Map;

public record BuildOptionsCatalog(
        List<BuildRoleRead> buildRoles,
        @NotNull List<BuildItemCategoryRead> categories,
        Map<String, Long> limits,
        @NotNull Map<String, List<BuildItemOptionRead>> options,
        Map<String, Number> researchUpgradeSlotEffects,
        @Min(0) @Max(8) Long researchUpgradeSlotGrant,
        List<BuildStatDefinitionRead> statDefinitions) { }
