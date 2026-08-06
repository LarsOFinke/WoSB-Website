// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record OutboundWebhookEventCatalogItem(
        @NotNull String defaultTemplate,
        @NotNull String description,
        @NotNull String group,
        @NotNull String key) { }
