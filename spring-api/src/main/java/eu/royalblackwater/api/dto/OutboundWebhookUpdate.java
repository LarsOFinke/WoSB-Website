// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record OutboundWebhookUpdate(
        Boolean broadcastEnabled,
        String discordUsername,
        String endpointUrl,
        @Size(max = 64) List<String> eventTypes,
        Boolean isActive,
        String messageTemplate,
        @NotNull @Size(min = 3, max = 120) String name,
        Long scopeId,
        String scopeType) { }
