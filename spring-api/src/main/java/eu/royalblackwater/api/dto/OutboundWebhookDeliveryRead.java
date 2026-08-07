// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record OutboundWebhookDeliveryRead(
        long attempts,
        @NotNull LocalDateTime createdAt,
        LocalDateTime deliveredAt,
        @NotNull String deliveryId,
        String errorMessage,
        @NotNull String eventType,
        long id,
        LocalDateTime lastAttemptAt,
        @NotNull String resourceId,
        @NotNull String resourceType,
        String responseBody,
        Long responseStatus,
        @NotNull String status,
        long webhookId,
        @NotNull String webhookName) { }
