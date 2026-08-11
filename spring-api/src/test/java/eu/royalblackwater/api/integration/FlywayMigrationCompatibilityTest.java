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
                    "select count(*) from " + schema + ".flyway_schema_history where version = '9'"))
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

    @Test
    void clearsOnlyTheFormerGenericWebhookTemplateDuringUpgrade() throws Exception {
        String schema = "legacy_webhook_template_upgrade";
        try (var connection = DriverManager.getConnection(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
             var statement = connection.createStatement()) {
            statement.execute("create schema " + schema);
        }

        Flyway beforeTemplateUpgrade = Flyway.configure()
                .dataSource(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword())
                .schemas(schema)
                .locations("classpath:db/migration")
                .target("8")
                .load();
        beforeTemplateUpgrade.migrate();

        try (var connection = DriverManager.getConnection(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
             var statement = connection.createStatement()) {
            statement.execute("set search_path to " + schema);
            statement.execute("""
                    insert into outbound_webhooks(name,endpoint_url,event_types_json,scope_type,message_template,
                        broadcast_enabled,is_active,created_at,updated_at,created_by_username)
                    values
                        ('Legacy','encrypted','[]','global',
                         'RBF event **{event}** for {resource.type} #{resource.id}.',false,true,now(),now(),'admin'),
                        ('Custom','encrypted','[]','global',
                         'Keep this administrator template',false,true,now(),now(),'admin')
                    """);
        }

        Flyway current = Flyway.configure()
                .dataSource(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword())
                .schemas(schema)
                .locations("classpath:db/migration")
                .load();
        assertThat(current.migrate().migrationsExecuted).isGreaterThanOrEqualTo(1);

        try (var connection = DriverManager.getConnection(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
             var statement = connection.createStatement()) {
            assertThat(count(statement, "select count(*) from " + schema
                    + ".outbound_webhooks where name='Legacy' and message_template is null"))
                    .isEqualTo(1);
            assertThat(count(statement, "select count(*) from " + schema
                    + ".outbound_webhooks where name='Custom' and message_template='Keep this administrator template'"))
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
