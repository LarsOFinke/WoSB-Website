package eu.royalblackwater.api.config;

import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.security")
public record SecurityProperties(List<String> allowedHosts, List<String> allowedOrigins) {
    public List<String> normalizeOrigins() {
        return allowedOrigins == null ? List.of() : allowedOrigins.stream()
                .map(String::strip)
                .filter(value -> !value.isEmpty())
                .map(value -> value.endsWith("/") ? value.substring(0, value.length() - 1) : value)
                .map(value -> value.toLowerCase(Locale.ROOT))
                .collect(Collectors.toUnmodifiableList());
    }
}
