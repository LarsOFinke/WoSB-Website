// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

public record SquadDetailRead(
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
        List<SquadMemberRead> members,
        @NotNull String name,
        @NotNull String slug,
        @NotNull LocalDateTime updatedAt) { }
