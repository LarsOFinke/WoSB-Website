// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record FleetPublicLeaderRead(
        @NotNull String displayName,
        @NotNull String role,
        @NotNull String roleLabel) { }
