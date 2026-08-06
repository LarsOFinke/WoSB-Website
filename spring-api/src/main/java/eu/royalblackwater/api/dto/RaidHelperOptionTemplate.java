// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record RaidHelperOptionTemplate(
        long id,
        boolean isDefault,
        @NotNull String name,
        long profileId,
        @NotNull String profileName,
        @NotNull String raidTemplateId) { }
