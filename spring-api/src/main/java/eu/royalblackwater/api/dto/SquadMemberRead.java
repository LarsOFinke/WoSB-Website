// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record SquadMemberRead(
        @NotNull String displayName,
        long fleetMembershipId,
        @NotNull String fleetRole,
        long id,
        @NotNull LocalDateTime joinedAt,
        String note,
        @NotNull String squadRole,
        long userId) { }
