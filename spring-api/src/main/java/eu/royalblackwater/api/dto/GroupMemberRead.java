// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record GroupMemberRead(
        BuildRead build,
        Long buildId,
        @NotNull @Size(min = 1, max = 120) String displayName,
        String fleetName,
        long id,
        boolean isActive,
        boolean isGuest,
        @NotNull LocalDateTime joinedAt,
        LocalDateTime leftAt,
        String note,
        ShipRead ship,
        Long shipId,
        String shipName,
        Long shipRate,
        Long userId) { }
