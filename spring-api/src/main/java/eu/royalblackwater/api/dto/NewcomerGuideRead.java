// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

public record NewcomerGuideRead(
        List<NewcomerGuideBlockRead> blocks,
        long id,
        @NotNull String intro,
        @NotNull String title,
        @NotNull LocalDateTime updatedAt,
        String updatedBy) { }
