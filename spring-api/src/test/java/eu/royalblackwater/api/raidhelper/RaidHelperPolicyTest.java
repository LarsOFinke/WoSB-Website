package eu.royalblackwater.api.raidhelper;

import eu.royalblackwater.api.raidhelper.service.RaidHelperPolicy;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RaidHelperPolicyTest {
    private final RaidHelperPolicy policy = new RaidHelperPolicy(new ObjectMapper());

    @Test
    void normalizesOfficialEndpointTimezoneCategoriesAndIdentifiers() {
        assertThat(policy.baseUrl("https://www.raid-helper.xyz/api/v4/")).isEqualTo("https://raid-helper.xyz/api/v4");
        assertThat(policy.timezone(" Europe/Berlin ")).isEqualTo("Europe/Berlin");
        assertThat(policy.categories(List.of("TRAINING", " training ", "other")))
                .containsExactly("other", "training");
        assertThat(policy.numericIdentifier(" 12345 ", "Server", true)).isEqualTo("12345");
        assertThat(policy.flag(null, true)).isTrue();
    }

    @Test
    void rejectsUnsafeEndpointsInvalidTimezoneAndPremiumPayloadFeatures() {
        assertBad(() -> policy.baseUrl("http://raid-helper.xyz/api/v4"));
        assertBad(() -> policy.baseUrl("https://example.com/api/v4"));
        assertBad(() -> policy.timezone("Mars/Olympus"));
        assertBad(() -> policy.category("unknown"));
        assertBad(() -> policy.numericIdentifier("12ab", "Server", true));
        assertBad(() -> policy.payloadTemplate("{\"title\":\"x\",\"date\":\"x\",\"time\":\"x\",\"advanced\":true}", null, false));
    }

    @Test
    void coversDefaultsOptionalIdentifiersFreePayloadAndPremiumPayloadBranches() {
        assertThat(policy.baseUrl(null)).isEqualTo(RaidHelperPolicy.DEFAULT_API_URL);
        assertThat(policy.timezone(null)).isEqualTo(RaidHelperPolicy.DEFAULT_TIMEZONE);
        assertThat(policy.categories(null)).isEmpty();
        assertThat(policy.categories(java.util.Arrays.asList(null, " ", "training", "TRAINING")))
                .containsExactly("training");
        assertThat(policy.numericIdentifier(" ", "Leader", false)).isNull();
        assertThat(policy.cleanName("  Fleet Ops  ", "Name")).isEqualTo("Fleet Ops");
        assertThat(policy.flag(Boolean.FALSE, true)).isFalse();
        assertThat(policy.normalizedTemplateId(null)).isNull();
        assertThat(policy.normalizedTemplateId(" standard ")).isNull();
        assertThat(policy.normalizedTemplateId(" custom ")).isEqualTo("custom");

        String free = policy.payloadTemplate(null, null, false);
        assertThat(free).contains("title", "date", "time");
        String premium = policy.payloadTemplate("{\"advanced\":true}", "custom", true);
        assertThat(premium).contains("advanced");

        assertBad(() -> policy.payloadTemplate("[]", null, false));
        assertBad(() -> policy.payloadTemplate("{\"title\":\"x\"}", null, false));
        assertBad(() -> policy.payloadTemplate(
                "{\"title\":\"x\",\"date\":\"x\",\"time\":\"x\",\"extra\":true}", null, false));
        assertBad(() -> policy.payloadTemplate(
                "{\"title\":\"x\",\"date\":\"x\",\"time\":\"x\"}", "custom", false));
        assertBad(() -> policy.cleanName(" ", "Name"));
    }

    @Test
    void rejectsApiUrlPathQueryFragmentAndUserInfoVariants() {
        assertBad(() -> policy.baseUrl("https://raid-helper.xyz/api/v3"));
        assertBad(() -> policy.baseUrl("https://raid-helper.xyz/api/v4?x=1"));
        assertBad(() -> policy.baseUrl("https://raid-helper.xyz/api/v4#fragment"));
        assertBad(() -> policy.baseUrl("https://user@raid-helper.xyz/api/v4"));
        assertBad(() -> policy.baseUrl("https://[bad"));
        assertBad(() -> policy.categories(java.util.List.of("invalid")));
    }

    private static void assertBad(org.assertj.core.api.ThrowableAssert.ThrowingCallable call) {
        assertThatThrownBy(call).isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(400));
    }
}
