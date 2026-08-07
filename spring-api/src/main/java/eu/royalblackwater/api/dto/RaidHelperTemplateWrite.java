// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record RaidHelperTemplateWrite(
        @Size(max = 2000) String announcementTemplate,
        List<String> categories,
        @Size(max = 4000) String descriptionTemplate,
        Boolean isActive,
        Boolean isDefault,
        @NotNull @Size(min = 1, max = 120) String name,
        @Size(min = 2, max = 12000) String payloadTemplateJson,
        long profileId,
        @Size(max = 80) String raidTemplateId,
        String scopeType,
        @Size(min = 1, max = 300) String titleTemplate,
        Boolean usesPremiumFeatures) { }
