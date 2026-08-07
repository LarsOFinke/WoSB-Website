// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record SquadCreate(
        String description,
        String focus,
        long leaderMembershipId,
        Long maxMembers,
        @NotNull @Size(min = 2, max = 120) String name) { }
