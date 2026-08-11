// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record StrategySummary(
        long id,
        @NotNull String title,
        String description,
        boolean isPublished,
        @NotNull String publicId,
        @NotNull FileRead backgroundFile,
        @NotNull LocalDateTime createdAt,
        @NotNull LocalDateTime updatedAt) { }
