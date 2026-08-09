package eu.royalblackwater.api.webhooks.dto;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.LocalDateTime;

public record WebhookDomainEvent(
        String eventType,
        String resourceType,
        String resourceId,
        String scopeType,
        Long scopeId,
        AuthenticatedUser actor,
        String summary,
        LocalDateTime occurredAt) {
}
