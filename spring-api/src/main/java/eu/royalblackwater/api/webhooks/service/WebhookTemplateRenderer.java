package eu.royalblackwater.api.webhooks.service;

import eu.royalblackwater.api.webhooks.dto.WebhookDomainEvent;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class WebhookTemplateRenderer {
    private static final Pattern PLACEHOLDER = Pattern.compile("\\{([a-z][a-z0-9_.]*)}");
    private static final Set<String> SUPPORTED = Set.of(
            "actor.display_name", "actor.username", "data.summary", "event",
            "occurred_at", "resource.id", "resource.type");

    private WebhookTemplateRenderer() { }

    public static Set<String> placeholders(String template) {
        java.util.LinkedHashSet<String> result = new java.util.LinkedHashSet<>();
        Matcher matcher = PLACEHOLDER.matcher(template == null ? "" : template);
        while (matcher.find()) result.add(matcher.group(1));
        return Set.copyOf(result);
    }

    public static boolean supports(String placeholder) {
        return SUPPORTED.contains(placeholder);
    }

    public static String render(String template, WebhookDomainEvent event) {
        String actor = event.actor() == null ? "RBF system" : event.actor().username();
        Map<String, String> values = Map.of(
                "actor.display_name", actor,
                "actor.username", actor,
                "data.summary", value(event.summary()),
                "event", event.eventType(),
                "occurred_at", event.occurredAt().toString() + "Z",
                "resource.id", event.resourceId(),
                "resource.type", event.resourceType());
        Matcher matcher = PLACEHOLDER.matcher(template);
        StringBuilder rendered = new StringBuilder();
        while (matcher.find()) {
            matcher.appendReplacement(rendered, Matcher.quoteReplacement(values.getOrDefault(matcher.group(1), "—")));
        }
        matcher.appendTail(rendered);
        return rendered.toString().strip();
    }

    private static String value(String value) {
        return value == null || value.isBlank() ? "No additional details." : value.strip();
    }
}
