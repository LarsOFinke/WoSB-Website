// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record DataSubjectRequestRead(
        @NotNull LocalDateTime createdAt,
        String details,
        Long handledByUserId,
        long id,
        @NotNull String requestType,
        String resolutionNote,
        LocalDateTime resolvedAt,
        @NotNull String status,
        long subjectUserId,
        @NotNull String subjectUsername) { }
