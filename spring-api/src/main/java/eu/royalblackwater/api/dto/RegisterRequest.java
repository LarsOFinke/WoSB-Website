// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotNull @Size(min = 1, max = 120) String displayName,
        String fleetApplicationNote,
        Long fleetId,
        @NotNull @Size(min = 12, max = 200) String password,
        @NotNull @Size(min = 3, max = 80) String username,
        Boolean wantsFleetMembership) { }
