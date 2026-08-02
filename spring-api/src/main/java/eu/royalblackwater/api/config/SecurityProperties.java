package eu.royalblackwater.api.config;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.security")
public record SecurityProperties(List<String> allowedHosts, List<String> allowedOrigins) {
}
