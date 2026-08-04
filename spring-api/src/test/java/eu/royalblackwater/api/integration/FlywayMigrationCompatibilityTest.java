package eu.royalblackwater.api.integration;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.DriverManager;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers(disabledWithoutDocker = true)
class FlywayMigrationCompatibilityTest {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16.4-alpine");

    @TempDir
    Path legacyMigrationDirectory;

    @Test
    void upgradesAnExistingV1HistoryWithoutChangingOrReapplyingIt() throws Exception {
        Path legacyMigration = legacyMigrationDirectory.resolve("V1__current_schema_baseline.sql");
        try (InputStream source = getClass().getResourceAsStream(
                "/db/migration/V1__current_schema_baseline.sql")) {
            assertThat(source).isNotNull();
            Files.copy(source, legacyMigration);
        }

        String schema = "legacy_v1_upgrade";
        try (var connection = DriverManager.getConnection(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
             var statement = connection.createStatement()) {
            statement.execute("create schema " + schema);
        }

        Flyway legacy = Flyway.configure()
                .dataSource(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword())
                .schemas(schema)
                .locations("filesystem:" + legacyMigrationDirectory.toAbsolutePath())
                .load();
        assertThat(legacy.migrate().migrationsExecuted).isEqualTo(1);

        Flyway current = Flyway.configure()
                .dataSource(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword())
                .schemas(schema)
                .locations("classpath:db/migration")
                .load();
        assertThat(current.migrate().migrationsExecuted).isEqualTo(5);
        current.validate();

        try (var connection = DriverManager.getConnection(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
             var statement = connection.createStatement()) {
            assertThat(count(statement,
                    "select count(*) from " + schema + ".flyway_schema_history where version = '1'"))
                    .isEqualTo(1);
            assertThat(count(statement,
                    "select count(*) from " + schema + ".flyway_schema_history where version = '2'"))
                    .isZero();
            assertThat(count(statement,
                    "select count(*) from " + schema + ".flyway_schema_history where version = '7'"))
                    .isEqualTo(1);
            assertThat(count(statement,
                    "select count(*) from information_schema.tables where table_schema = '" + schema
                            + "' and table_name = 'users'"))
                    .isEqualTo(1);
        }
    }

    private static long count(java.sql.Statement statement, String query) throws Exception {
        try (var result = statement.executeQuery(query)) {
            result.next();
            return result.getLong(1);
        }
    }
}
