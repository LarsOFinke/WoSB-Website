// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record RegistrationRequestPublic(
        @NotNull LocalDateTime createdAt,
        @NotNull String displayName,
        String fleetApplicationNote,
        Long fleetId,
        long id,
        @NotNull String status,
        @NotNull String username,
        Boolean wantsFleetMembership) { }
