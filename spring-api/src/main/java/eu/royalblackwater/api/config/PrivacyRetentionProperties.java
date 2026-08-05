package eu.royalblackwater.api.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.privacy")
public record PrivacyRetentionProperties(
        Duration cookieConsentRetention,
        Duration resolvedRequestRetention,
        Duration retentionInterval) {

    public PrivacyRetentionProperties {
        requirePositive(cookieConsentRetention, "cookie-consent-retention");
        requirePositive(resolvedRequestRetention, "resolved-request-retention");
        requirePositive(retentionInterval, "retention-interval");
    }

    private static void requirePositive(Duration value, String name) {
        if (value == null || value.isZero() || value.isNegative()) {
            throw new IllegalArgumentException("rbf.privacy." + name + " must be positive");
        }
    }
}
