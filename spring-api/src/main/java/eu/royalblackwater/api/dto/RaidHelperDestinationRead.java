// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;

public record RaidHelperDestinationRead(
        List<String> categories,
        @NotNull @Size(min = 5, max = 32) @Pattern(regexp = "^[0-9]+$") String channelId,
        @NotNull LocalDateTime createdAt,
        long id,
        Boolean isActive,
        Boolean isDefault,
        @NotNull @Size(min = 1, max = 120) String name,
        long profileId,
        @NotNull String profileName,
        @NotNull String scopeType,
        Long squadId,
        String squadName,
        @NotNull LocalDateTime updatedAt) { }
