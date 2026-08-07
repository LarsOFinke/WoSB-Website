// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record PrivacyContactRead(
        @NotNull LocalDateTime createdAt,
        Long handledByUserId,
        long id,
        @NotNull String message,
        @NotNull String replyEmail,
        String resolutionNote,
        LocalDateTime resolvedAt,
        @NotNull String status,
        @NotNull String subject,
        Long userId) { }
