// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public record NewcomerGuideBlockRead(
        @NotNull String blockType,
        String body,
        long id,
        List<NewcomerGuideResourceRead> resources,
        @NotNull String title) { }
