// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record StrategyRead(
        long id,
        long ownerId,
        @NotNull String title,
        String description,
        @NotNull String overlayJson,
        boolean isPublished,
        @NotNull String publicId,
        @NotNull FileRead backgroundFile,
        @NotNull LocalDateTime createdAt,
        @NotNull LocalDateTime updatedAt,
        LocalDateTime publishedAt) { }
