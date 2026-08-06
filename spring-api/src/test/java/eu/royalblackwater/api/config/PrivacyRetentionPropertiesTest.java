package eu.royalblackwater.api.config;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThatIllegalArgumentException;

class PrivacyRetentionPropertiesTest {
    @Test
    void rejectsMissingOrNonPositiveRetentionPeriods() {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new PrivacyRetentionProperties(null, Duration.ofDays(1), Duration.ofHours(1)))
                .withMessageContaining("cookie-consent-retention");
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new PrivacyRetentionProperties(
                        Duration.ofDays(1), Duration.ZERO, Duration.ofHours(1)))
                .withMessageContaining("resolved-request-retention");
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new PrivacyRetentionProperties(
                        Duration.ofDays(1), Duration.ofDays(1), Duration.ofSeconds(-1)))
                .withMessageContaining("retention-interval");
    }
}
