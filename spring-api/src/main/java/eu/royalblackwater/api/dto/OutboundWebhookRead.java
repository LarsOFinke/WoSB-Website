// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

public record OutboundWebhookRead(
        boolean broadcastEnabled,
        @NotNull LocalDateTime createdAt,
        @NotNull String createdByUsername,
        String discordUsername,
        @NotNull String endpointUrl,
        @NotNull List<String> eventTypes,
        long id,
        boolean isActive,
        LocalDateTime lastFailureAt,
        LocalDateTime lastSuccessAt,
        String messageTemplate,
        @NotNull String name,
        Long scopeId,
        @NotNull String scopeType,
        @NotNull LocalDateTime updatedAt) { }
