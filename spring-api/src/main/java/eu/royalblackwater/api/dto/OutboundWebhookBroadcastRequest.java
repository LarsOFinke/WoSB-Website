// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record OutboundWebhookBroadcastRequest(
        String discordUsername,
        @NotNull @Size(min = 1, max = 2000) String message,
        @NotNull @Size(min = 1, max = 50) List<Long> webhookIds) { }
