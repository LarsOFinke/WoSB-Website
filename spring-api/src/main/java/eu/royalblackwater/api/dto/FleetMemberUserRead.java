// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record FleetMemberUserRead(
        @NotNull String displayName,
        long id,
        @NotNull String role,
        @NotNull String username) { }
