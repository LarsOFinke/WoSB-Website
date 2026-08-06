// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record RaidHelperProfileWrite(
        @Size(max = 200) String apiBaseUrl,
        String apiKey,
        String defaultLeaderId,
        Boolean isActive,
        @NotNull @Size(min = 1, max = 120) String name,
        @NotNull @Size(min = 5, max = 32) @Pattern(regexp = "^[0-9]+$") String serverId,
        @Size(min = 1, max = 80) String timezone) { }
