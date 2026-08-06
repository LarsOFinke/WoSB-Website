// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record BackupDiscoveryRequest(
        @NotNull @Size(min = 1, max = 253) String host,
        @Min(1) @Max(65535) Long port) { }
