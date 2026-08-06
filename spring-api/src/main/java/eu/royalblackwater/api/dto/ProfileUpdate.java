// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record ProfileUpdate(
        String availability,
        String discordHandle,
        @NotNull @Size(min = 1, max = 120) String displayName,
        String fleetName,
        String note,
        String preferredFocus,
        @Size(max = 10) List<Long> preferredRoleIds,
        @Size(max = 20) List<Long> preferredShipIds,
        String timezone) { }
