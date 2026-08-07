// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.util.List;

public record RaidHelperDestinationWrite(
        List<String> categories,
        @NotNull @Size(min = 5, max = 32) @Pattern(regexp = "^[0-9]+$") String channelId,
        Boolean isActive,
        Boolean isDefault,
        @NotNull @Size(min = 1, max = 120) String name,
        long profileId,
        @NotNull String scopeType,
        Long squadId) { }
