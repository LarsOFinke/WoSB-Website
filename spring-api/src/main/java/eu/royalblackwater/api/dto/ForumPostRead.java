// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

public record ForumPostRead(
        List<FileRead> attachments,
        @NotNull UserReferenceRead author,
        long authorId,
        @NotNull String body,
        @NotNull LocalDateTime createdAt,
        long id,
        long threadId,
        @NotNull LocalDateTime updatedAt) { }
