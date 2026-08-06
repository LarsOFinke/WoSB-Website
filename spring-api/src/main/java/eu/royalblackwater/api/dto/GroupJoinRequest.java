// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record GroupJoinRequest(
        Long buildId,
        @NotNull @Size(min = 1, max = 120) String displayName,
        String fleetName,
        String note,
        Long shipId,
        String shipName,
        Long shipRate) { }
