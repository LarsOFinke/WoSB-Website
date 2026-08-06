// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record HomeVoicePolicyRead(
        @NotNull @Size(min = 1, max = 64) String competitive,
        @NotNull @Size(min = 1, max = 64) String general) { }
