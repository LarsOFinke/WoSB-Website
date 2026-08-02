package eu.royalblackwater.api.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.session")
public record SessionProperties(String cookieName, boolean secure, String sameSite, Duration ttl) {
}
