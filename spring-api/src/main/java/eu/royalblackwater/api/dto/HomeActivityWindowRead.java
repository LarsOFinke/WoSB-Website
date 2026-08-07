// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record HomeActivityWindowRead(
        @NotNull @Size(min = 1, max = 64) String timezone,
        @NotNull @Size(min = 1, max = 64) String main,
        @NotNull @Size(min = 1, max = 64) String portBattles) { }
