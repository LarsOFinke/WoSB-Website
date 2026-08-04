package eu.royalblackwater.api.config;

import java.util.Arrays;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.secrets")
public record SecretEncryptionProperties(String encryptionKeys) {
    public List<String> configuredKeys() {
        if (encryptionKeys == null || encryptionKeys.isBlank()) {
            return List.of();
        }
        return Arrays.stream(encryptionKeys.split(","))
                .map(String::strip)
                .filter(value -> !value.isEmpty())
                .distinct()
                .toList();
    }
}
