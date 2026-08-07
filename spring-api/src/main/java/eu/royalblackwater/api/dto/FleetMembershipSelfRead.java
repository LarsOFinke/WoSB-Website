// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record FleetMembershipSelfRead(
        String adminNote,
        String assignment,
        String availability,
        String discordHandle,
        @NotNull FleetMembershipFleetRead fleet,
        long fleetId,
        long id,
        @NotNull LocalDateTime joinedAt,
        FleetMembershipManagementRead management,
        String note,
        String preferredRoles,
        String preferredShips,
        @NotNull String role,
        @NotNull String status,
        String timezone,
        @NotNull LocalDateTime updatedAt,
        @NotNull FleetMemberUserRead user,
        long userId) { }
