// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

public record AuditLogRead(
        @NotNull String action,
        @NotNull String actorRole,
        Long actorUserId,
        @NotNull String actorUsername,
        List<String> changedFields,
        @NotNull LocalDateTime createdAt,
        @NotNull String entityId,
        @NotNull String entityType,
        long id,
        @NotNull String summary) { }
