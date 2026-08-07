// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record SquadSummaryRead(
        boolean canAdminister,
        boolean canManage,
        @NotNull LocalDateTime createdAt,
        String currentUserRole,
        String description,
        long fleetId,
        String focus,
        long id,
        boolean isActive,
        boolean isMember,
        SquadMemberRead leader,
        Long maxMembers,
        long memberCount,
        @NotNull String name,
        @NotNull String slug,
        @NotNull LocalDateTime updatedAt) { }
