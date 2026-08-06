// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record RaidHelperProfileRead(
        @NotNull String apiBaseUrl,
        boolean apiKeyConfigured,
        @NotNull LocalDateTime createdAt,
        @NotNull String createdByUsername,
        String defaultLeaderId,
        long id,
        boolean isActive,
        @NotNull String name,
        @NotNull String serverId,
        @NotNull String timezone,
        @NotNull LocalDateTime updatedAt) { }
