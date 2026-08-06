// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record DataSubjectRequestResolve(
        @NotNull String decision,
        @NotNull @Size(min = 3, max = 4000) String resolutionNote) { }
