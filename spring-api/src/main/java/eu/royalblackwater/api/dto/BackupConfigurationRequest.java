// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record BackupConfigurationRequest(
        @NotNull @Size(min = 1, max = 253) String host,
        @NotNull @Size(min = 32, max = 8192) String hostKey,
        @Min(1) @Max(65535) Long port,
        String privateKey,
        @NotNull @Size(min = 1, max = 512) String remoteDirectory,
        @NotNull @Size(min = 1, max = 64) String username) { }
