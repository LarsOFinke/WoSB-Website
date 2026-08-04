package eu.royalblackwater.api.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("rbf.bootstrap-admin")
public record BootstrapAdminProperties(String username, String password, String displayName) {
    public BootstrapAdminProperties {
        username = normalized(username, "admin");
        displayName = normalized(displayName, "RBF Command");
        password = password == null ? "" : password;
    }

    public boolean configured() {
        return !password.isBlank();
    }

    private static String normalized(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value.strip();
    }
}
