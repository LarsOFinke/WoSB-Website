// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record ProfileShipOptionRead(
        @Min(1) long id,
        @NotNull @Size(min = 1, max = 160) String name,
        @Min(0) long rate) { }
