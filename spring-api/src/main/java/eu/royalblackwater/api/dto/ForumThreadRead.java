// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

public record ForumThreadRead(
        @NotNull String category,
        @NotNull LocalDateTime createdAt,
        long id,
        @NotNull LocalDateTime lastActivityAt,
        @NotNull UserReferenceRead owner,
        long ownerId,
        List<ForumPostRead> posts,
        long replyCount,
        @NotNull String title,
        @NotNull LocalDateTime updatedAt) { }
