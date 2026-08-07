// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record RaidHelperEventLinkRead(
        long destinationId,
        @NotNull String destinationName,
        String errorMessage,
        String externalEventId,
        long id,
        @NotNull String lastOperation,
        @NotNull String profileName,
        @NotNull String status,
        LocalDateTime syncedAt,
        long templateId,
        @NotNull String templateName) { }
