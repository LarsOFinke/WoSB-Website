package eu.royalblackwater.api.integration;

import static org.assertj.core.api.Assertions.assertThat;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers(disabledWithoutDocker = true)
class ApplicationIntegrationTest {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16.4-alpine");

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        Path runtime = Path.of(System.getProperty("java.io.tmpdir"), "rbf-integration-test");
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("rbf.secrets.encryption-keys",
                () -> "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=");
        registry.add("rbf.bootstrap-admin.password", () -> "Integration-Test-Admin-Password-42!");
        registry.add("rbf.session.secure", () -> false);
        registry.add("rbf.scheduling.enabled", () -> false);
        registry.add("rbf.storage.upload-root", () -> runtime.resolve("uploads").toString());
        registry.add("rbf.operations.control-root", () -> runtime.resolve("control").toString());
    }

    @Autowired
    JdbcQueryService jdbc;

    @LocalServerPort
    int port;

    @Test
    void migratesSeedsAndStartsTheCompleteApplication() {
        assertThat(jdbc.count("select count(*) from flyway_schema_history where success=true", Map.of()))
                .isPositive();
        assertThat(jdbc.count("select count(*) from site_roles", Map.of())).isPositive();
        assertThat(jdbc.count("select count(*) from users where is_bootstrap_admin=true", Map.of()))
                .isEqualTo(1);
    }

    @Test
    void exposesHealthAndReadinessButProtectsMemberApis() throws Exception {
        HttpResponse<String> health = get("/api/health");
        HttpResponse<String> readiness = get("/api/health/ready");
        HttpResponse<String> protectedApi = get("/api/builds");

        assertThat(health.statusCode()).isEqualTo(200);
        assertThat(health.body()).contains("\"status\":\"ok\"");
        assertThat(readiness.statusCode()).isEqualTo(200);
        assertThat(readiness.body()).contains("\"status\":\"ready\"");
        assertThat(protectedApi.statusCode()).isEqualTo(401);
    }

    @Test
    void exposesRegistrationAndOfficialFleetWithoutAuthentication() throws Exception {
        HttpResponse<String> fleet = get("/api/fleets/public/official");
        assertThat(fleet.statusCode()).isIn(200, 404);

        HttpRequest register = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/api/auth/register"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(
                        "{\"username\":\"integration-public-route\",\"password\":\"Integration-Password-42!\","
                                + "\"displayName\":\"Integration Public Route\",\"wantsFleetMembership\":false}"))
                .build();
        HttpResponse<String> registration = HttpClient.newHttpClient().send(register, HttpResponse.BodyHandlers.ofString());
        // Without the browser's XSRF header Spring rejects the unsafe request
        // with 403; it must never be rejected as unauthenticated (401).
        assertThat(registration.statusCode()).isIn(202, 403, 409);
    }

    private HttpResponse<String> get(String path) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:" + port + path))
                .GET()
                .build();
        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
    }
}
