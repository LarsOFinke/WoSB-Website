package eu.royalblackwater.api.webhooks.service;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.webhooks.dto.WebhookDomainEvent;
import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class WebhookTemplateRendererTest {
    @Test
    void rendersEverySupportedValueWithoutLeavingTemplateSyntax() {
        AuthenticatedUser actor = new AuthenticatedUser(7, "captain", "admin", true, true, false);
        WebhookDomainEvent event = new WebhookDomainEvent("fleet.created", "fleet", "42",
                "fleet", 42L, actor, "Fleet Aurora was created.",
                LocalDateTime.of(2026, 8, 9, 19, 30));

        String rendered = WebhookTemplateRenderer.render(
                "{event}|{resource.type}|{resource.id}|{actor.username}|{actor.display_name}|{data.summary}|{occurred_at}",
                event);

        assertThat(rendered).isEqualTo(
                "fleet.created|fleet|42|captain|captain|Fleet Aurora was created.|2026-08-09T19:30Z");
        assertThat(rendered).doesNotContain("{");
    }

    @Test
    void systemEventsDoNotRequireAUser() {
        WebhookDomainEvent event = new WebhookDomainEvent("system.update.result", "system_update", "update",
                null, null, null, "Update completed.", LocalDateTime.of(2026, 8, 9, 20, 0));

        assertThat(WebhookTemplateRenderer.render("{actor.display_name}: {data.summary}", event))
                .isEqualTo("RBF system: Update completed.");
    }
}
