// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record PrivacyContactResolve(
        @NotNull String decision,
        @NotNull @Size(min = 3, max = 4000) String resolutionNote) { }
