// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public record FleetPublicRead(
        Long activeMembersCount,
        String description,
        @NotNull String focus,
        long id,
        List<FleetPublicLeaderRead> leaders,
        @NotNull String name,
        @NotNull String slug,
        String standingOrders) { }
