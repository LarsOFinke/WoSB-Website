package eu.royalblackwater.api.webhooks;

import eu.royalblackwater.api.webhooks.service.WebhookPolicy;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class WebhookPolicyTest {
    private final WebhookPolicy policy = new WebhookPolicy();

    @Test
    void normalizesEventsAndScopes() {
        assertThat(policy.events(List.of("build.created", "build.created", "build.updated"), false))
                .containsExactly("build.created", "build.updated");
        assertThat(policy.scope(null, null)).isEqualTo(new WebhookPolicy.Scope("global", null));
        assertThat(policy.scope(" FLEET ", 9L)).isEqualTo(new WebhookPolicy.Scope("fleet", 9L));
    }

    @Test
    void rejectsUnknownEventsInvalidScopesAndNonDiscordEndpoints() {
        assertBad(() -> policy.events(List.of(), false));
        assertBad(() -> policy.events(List.of("unknown.event"), false));
        assertBad(() -> policy.scope("squad", null));
        assertBad(() -> policy.scope("unknown", 1L));
        assertBad(() -> policy.endpoint("https://example.com/api/webhooks/1/token"));
        assertBad(() -> policy.endpoint("http://discord.com/api/webhooks/1/token"));
        assertBad(() -> policy.template("Hello {data.private_note}"));
    }

    @Test
    void acceptsOnlyDocumentedTemplatePlaceholders() {
        assertThat(policy.template("{event}: {data.summary} by {actor.display_name}"))
                .isEqualTo("{event}: {data.summary} by {actor.display_name}");
        assertThat(policy.template("  ")).isNull();
    }

    private static void assertBad(org.assertj.core.api.ThrowableAssert.ThrowingCallable call) {
        assertThatThrownBy(call).isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(400));
    }
}
