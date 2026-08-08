package eu.royalblackwater.api.integration;

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
import static org.assertj.core.api.Assertions.assertThat;

@Testcontainers(disabledWithoutDocker = true)
class FlywayMigrationCompatibilityTest {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = PostgresTestContainerFactory.create();

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
        int pendingBeforeUpgrade = current.info().pending().length;
        assertThat(pendingBeforeUpgrade).isPositive();
        assertThat(current.migrate().migrationsExecuted).isEqualTo(pendingBeforeUpgrade);
        assertThat(current.migrate().migrationsExecuted).isZero();
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
                    "select count(*) from " + schema + ".flyway_schema_history where version = '8'"))
                    .isEqualTo(1);
            assertThat(count(statement,
                    "select count(*) from information_schema.tables where table_schema = '" + schema
                            + "' and table_name = 'users'"))
                    .isEqualTo(1);
            assertThat(count(statement,
                    "select count(*) from information_schema.columns where table_schema = '" + schema
                            + "' and table_name = 'builds' and column_name in "
                            + "('printout_cache_key','printout_source_updated_at')"))
                    .isEqualTo(2);
        }
    }

    private static long count(java.sql.Statement statement, String query) throws Exception {
        try (var result = statement.executeQuery(query)) {
            result.next();
            return result.getLong(1);
        }
    }
}
