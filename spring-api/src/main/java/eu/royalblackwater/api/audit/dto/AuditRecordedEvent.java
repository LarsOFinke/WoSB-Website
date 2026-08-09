package eu.royalblackwater.api.audit.dto;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.LocalDateTime;

public record AuditRecordedEvent(
        String action,
        AuthenticatedUser actor,
        String entityId,
        String entityType,
        LocalDateTime occurredAt,
        Long scopeId,
        String scopeType,
        String summary) {
}
