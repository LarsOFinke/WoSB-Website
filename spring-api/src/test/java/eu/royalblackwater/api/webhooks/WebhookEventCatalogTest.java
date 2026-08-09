package eu.royalblackwater.api.webhooks;

import eu.royalblackwater.api.webhooks.service.WebhookEventCatalog;
import eu.royalblackwater.api.webhooks.service.WebhookTemplateRenderer;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class WebhookEventCatalogTest {
    @Test
    void generatedWebhookCatalogHasUniqueKeysAndMatchingTypeSet() {
        assertThat(WebhookEventCatalog.ALL).isNotEmpty();
        Set<String> keys = WebhookEventCatalog.ALL.stream().map(event -> {
            assertThat(event.key()).matches("[a-z0-9_.-]+");
            assertThat(event.group()).isNotBlank();
            assertThat(event.description()).isNotBlank();
            assertThat(event.defaultTemplate()).contains("{event}").doesNotContain("RBF event **{event}**");
            assertThat(WebhookTemplateRenderer.placeholders(event.defaultTemplate()))
                    .allMatch(WebhookTemplateRenderer::supports);
            return event.key();
        }).collect(Collectors.toSet());

        assertThat(keys).hasSameSizeAs(WebhookEventCatalog.ALL);
        assertThat(WebhookEventCatalog.TYPES).isEqualTo(keys);
        assertThat(WebhookEventCatalog.ALL.stream().map(event -> event.defaultTemplate()).distinct())
                .hasSameSizeAs(WebhookEventCatalog.ALL);
    }
}
