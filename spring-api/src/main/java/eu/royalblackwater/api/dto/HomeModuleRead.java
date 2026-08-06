// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record HomeModuleRead(
        @NotNull @Size(min = 1, max = 64) String key,
        @NotNull @Size(min = 1, max = 32) String status,
        @NotNull @Size(min = 1, max = 32) String access) { }
