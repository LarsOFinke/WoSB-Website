// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record FileRead(
        @NotNull LocalDateTime createdAt,
        long id,
        Boolean isPublic,
        @NotNull String mimeType,
        @NotNull String originalName,
        Long ownerId,
        @NotNull String publicUrl,
        @NotNull String relativePath,
        long sizeBytes,
        @NotNull String storedName,
        @NotNull String usageContext) { }
