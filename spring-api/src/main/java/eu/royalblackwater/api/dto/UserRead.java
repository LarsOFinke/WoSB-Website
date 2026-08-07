// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

public record UserRead(
        String availability,
        Boolean canGrantAdmin,
        @NotNull LocalDateTime createdAt,
        String discordHandle,
        @NotNull String displayName,
        Long fleetId,
        Long fleetMembershipId,
        String fleetMembershipRole,
        String fleetMembershipStatus,
        String fleetName,
        long id,
        boolean isActive,
        Boolean isBootstrapAdmin,
        String note,
        String preferredFocus,
        List<Long> preferredRoleIds,
        List<Long> preferredShipIds,
        @NotNull String role,
        String timezone,
        @NotNull String username) { }
