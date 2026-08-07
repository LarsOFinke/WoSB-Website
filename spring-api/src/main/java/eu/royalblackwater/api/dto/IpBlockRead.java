// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record IpBlockRead(
        @NotNull LocalDateTime createdAt,
        Long createdByUserId,
        @NotNull String createdByUsername,
        LocalDateTime expiresAt,
        long id,
        @NotNull String ipAddress,
        boolean isActive,
        boolean isExpired,
        boolean isTemporary,
        String notes,
        @NotNull String reason,
        String unblockReason,
        LocalDateTime unblockedAt,
        Long unblockedByUserId,
        String unblockedByUsername) { }
