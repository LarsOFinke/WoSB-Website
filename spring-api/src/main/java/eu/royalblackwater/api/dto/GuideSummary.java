// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record GuideSummary(
        Long attachmentCount,
        Long buildReferenceCount,
        @NotNull String category,
        @NotNull LocalDateTime createdAt,
        long id,
        @NotNull UserReferenceRead owner,
        long ownerId,
        String summary,
        @NotNull String title,
        @NotNull LocalDateTime updatedAt) { }
