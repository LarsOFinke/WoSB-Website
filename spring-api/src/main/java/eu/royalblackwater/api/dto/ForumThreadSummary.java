// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record ForumThreadSummary(
        @NotNull String category,
        @NotNull LocalDateTime createdAt,
        long id,
        @NotNull LocalDateTime lastActivityAt,
        @NotNull UserReferenceRead owner,
        long ownerId,
        long replyCount,
        @NotNull String title,
        @NotNull LocalDateTime updatedAt) { }
