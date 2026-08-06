package eu.royalblackwater.api.webhooks.dto;

/** Internal definition of a supported outbound webhook event. */
public record WebhookEventDefinition(
        String defaultTemplate,
        String description,
        String group,
        String key) { }
