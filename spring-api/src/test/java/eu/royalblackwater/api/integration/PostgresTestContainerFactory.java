package eu.royalblackwater.api.integration;

import org.testcontainers.containers.PostgreSQLContainer;

final class PostgresTestContainerFactory {
    private static final String IMAGE = "postgres:16.4-alpine";
    private static final int STARTUP_ATTEMPTS = 3;

    private PostgresTestContainerFactory() {
    }

    static PostgreSQLContainer<?> create() {
        PostgreSQLContainer<?> container = new PostgreSQLContainer<>(IMAGE);
        container.setStartupAttempts(STARTUP_ATTEMPTS);
        return container;
    }
}
