package eu.royalblackwater.api.integration;

import static org.assertj.core.api.Assertions.assertThat;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.PasswordHasher;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.util.Map;
import java.util.regex.Pattern;
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

    @Autowired
    PasswordHasher passwords;

    @LocalServerPort
    int port;

    @Test
    void migratesSeedsAndStartsTheCompleteApplication() {
        assertThat(jdbc.count("select count(*) from flyway_schema_history where success=true", Map.of()))
                .isPositive();
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='1'", Map.of()))
                .isZero();
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='2'", Map.of()))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from flyway_schema_history where version='7'", Map.of()))
                .isEqualTo(1);
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

        HttpResponse<String> csrfBootstrap = get("/api/auth/me");
        String setCookie = csrfBootstrap.headers().firstValue("set-cookie").orElseThrow();
        var xsrfMatcher = Pattern.compile("(?:^|;\\s*)XSRF-TOKEN=([^;]+)").matcher(setCookie);
        assertThat(xsrfMatcher.find()).isTrue();
        String xsrf = xsrfMatcher.group(1);
        HttpRequest register = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/api/auth/register"))
                .header("Content-Type", "application/json")
                .header("Cookie", "XSRF-TOKEN=" + xsrf)
                .header("X-XSRF-TOKEN", xsrf)
                .POST(HttpRequest.BodyPublishers.ofString(
                        "{\"username\":\"integration-public-route\",\"password\":\"Integration-Password-42!\","
                                + "\"display_name\":\"Integration Public Route\",\"wants_fleet_membership\":false}"))
                .build();
        HttpResponse<String> registration = HttpClient.newHttpClient().send(register, HttpResponse.BodyHandlers.ofString());
        assertThat(registration.statusCode()).isIn(202, 409);
    }

    @Test
    void enforcesAuthenticationAdminRoleRequestBoundaryAndCsrf() throws Exception {
        assertThat(get("/api/admin/users").statusCode()).isEqualTo(401);

        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        assertThat(get("/api/admin/users", administrator.sessionCookie()).statusCode()).isEqualTo(200);

        String memberUsername = "integration-member";
        String memberPassword = "Integration-Member-Password-42!";
        createMember(memberUsername, memberPassword);
        SessionCookies member = login(memberUsername, memberPassword);
        assertThat(get("/api/admin/users", member.sessionCookie()).statusCode()).isEqualTo(403);

        HttpResponse<String> missingCsrf = post(
                "/api/auth/change-password",
                "{\"current_password\":\"wrong\",\"new_password\":\"Different-Password-42!\"}",
                member.sessionCookie(), null, localOrigin());
        assertThat(missingCsrf.statusCode()).isEqualTo(403);

        HttpResponse<String> invalidCurrentPassword = post(
                "/api/auth/change-password",
                "{\"current_password\":\"wrong\",\"new_password\":\"Different-Password-42!\"}",
                member.cookieHeader(), member.csrfToken(), localOrigin());
        assertThat(invalidCurrentPassword.statusCode()).isEqualTo(400);
        assertThat(invalidCurrentPassword.body()).doesNotContain("Exception", "stackTrace");

        HttpResponse<String> crossSiteLogin = post(
                "/api/auth/login",
                "{\"username\":\"admin\",\"password\":\"Integration-Test-Admin-Password-42!\"}",
                null, null, "https://untrusted.example");
        assertThat(crossSiteLogin.statusCode()).isEqualTo(403);
    }

    @Test
    void rejectsInvalidPublicMutationWithoutLeakingImplementationDetails() throws Exception {
        HttpResponse<String> response = post("/api/auth/register", "{}", null, null, localOrigin());

        assertThat(response.statusCode()).isEqualTo(400);
        assertThat(response.body()).doesNotContain("Exception", "stackTrace", "org.springframework");
    }

    @Test
    void acceptsIsoDatesAndUtcTimestampsProducedByTheFrontend() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");

        for (String path : new String[] {
                "/api/admin/registration-requests?from_date=2030-01-01&to_date=2030-02-01",
                "/api/admin/audit-logs?from_date=2030-01-01&to_date=2030-02-01",
                "/api/admin/logs/security-dashboard?from_date=2030-01-01&to_date=2030-02-01"
        }) {
            assertThat(get(path, administrator.sessionCookie()).statusCode()).as(path).isEqualTo(200);
        }

        HttpResponse<String> calendar = get(
                "/api/calendar/events?start=2030-01-01T00:00:00.000Z&end=2030-02-01T00:00:00.000Z",
                administrator.sessionCookie());
        assertThat(calendar.statusCode()).isEqualTo(200);

        HttpResponse<String> invalidCalendar = get(
                "/api/calendar/events?start=not-a-timestamp", administrator.sessionCookie());
        assertThat(invalidCalendar.statusCode()).isEqualTo(400);
        assertThat(invalidCalendar.body()).doesNotContain("Exception", "stackTrace", "org.springframework");

        HttpResponse<String> created = post(
                "/api/calendar/events",
                "{\"title\":\"UTC contract integration event\",\"category\":\"other\","
                        + "\"start_at\":\"2030-01-15T18:00:00.000Z\","
                        + "\"end_at\":\"2030-01-15T20:00:00.000Z\","
                        + "\"raid_helper_enabled\":false}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertThat(created.statusCode()).isEqualTo(201);
        assertThat(created.body()).contains("\"title\":\"UTC contract integration event\"");
    }

    @Test
    void loadsEveryStaffOverviewDataSourceWithoutServerErrors() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");

        for (String path : new String[] {
                "/api/admin/registration-requests?status=pending",
                "/api/calendar/events?start=2030-01-01T00:00:00.000Z&end=2030-04-01T00:00:00.000Z",
                "/api/admin/forum/threads",
                "/api/admin/guides",
                "/api/groups",
                "/api/admin/builds",
                "/api/admin/build-roles",
                "/api/admin/users",
                "/api/admin/master-data/overview",
                "/api/admin/master-data/taxonomy",
                "/api/admin/master-data/categories",
                "/api/admin/master-data/options",
                "/api/admin/master-data/ships",
                "/api/admin/logs/security-dashboard?sort=threat&limit=100",
                "/api/admin/ip-blocks/summary"
        }) {
            assertThat(get(path, administrator.sessionCookie()).statusCode()).as(path).isEqualTo(200);
        }
    }

    @Test
    void persistsAndReloadsAnonymousCookieConsent() throws Exception {
        HttpResponse<String> initial = get("/api/privacy/cookie-consent");
        assertThat(initial.statusCode()).isEqualTo(200);
        assertThat(initial.body()).contains("\"has_decision\":false");

        HttpResponse<String> saved = post(
                "/api/privacy/cookie-consent",
                "{\"necessary\":true,\"preferences\":true,\"analytics\":false,\"external_media\":true}",
                null, null, localOrigin());
        assertThat(saved.statusCode()).isEqualTo(200);
        assertThat(saved.body()).contains("\"has_decision\":true", "\"preferences\":true", "\"external_media\":true");

        HttpResponse<String> reloaded = get(
                "/api/privacy/cookie-consent", cookie(saved, "rbf_cookie_consent"));
        assertThat(reloaded.statusCode()).isEqualTo(200);
        assertThat(reloaded.body()).contains("\"has_decision\":true", "\"preferences\":true", "\"analytics\":false",
                "\"external_media\":true");
    }

    private HttpResponse<String> get(String path) throws Exception {
        return get(path, null);
    }

    private HttpResponse<String> get(String path, String cookie) throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(localOrigin() + path)).GET();
        if (cookie != null) request.header("Cookie", cookie);
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> post(String path, String body, String cookie, String csrf, String origin)
            throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(localOrigin() + path))
                .header("Content-Type", "application/json")
                .header("Origin", origin)
                .POST(HttpRequest.BodyPublishers.ofString(body));
        if (cookie != null) request.header("Cookie", cookie);
        if (csrf != null) request.header("X-XSRF-TOKEN", csrf);
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private SessionCookies login(String username, String password) throws Exception {
        HttpResponse<String> login = post("/api/auth/login",
                "{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}",
                null, null, localOrigin());
        assertThat(login.statusCode()).isEqualTo(200);
        String sessionCookie = cookie(login, "rbf_hub_session");

        HttpResponse<String> csrfBootstrap = get("/api/auth/me", sessionCookie);
        String csrfToken = cookieValue(csrfBootstrap, "XSRF-TOKEN");
        return new SessionCookies(sessionCookie, csrfToken);
    }

    private void createMember(String username, String password) {
        jdbc.update("delete from users where username=:username", Map.of("username", username));
        long userId = jdbc.insertReturningId("""
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:password,(select id from site_roles where code='user'),true,false,current_timestamp,current_timestamp)
                returning id
                """, Map.of("username", username, "password", passwords.hash(password)));
        jdbc.update("""
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,'Integration Member',current_timestamp,current_timestamp)
                """, Map.of("userId", userId));
    }

    private static String cookie(HttpResponse<String> response, String name) {
        return name + "=" + cookieValue(response, name);
    }

    private static String cookieValue(HttpResponse<String> response, String name) {
        Pattern pattern = Pattern.compile("(?:^|;\\s*)" + Pattern.quote(name) + "=([^;]+)");
        return response.headers().allValues("set-cookie").stream()
                .map(pattern::matcher)
                .filter(java.util.regex.Matcher::find)
                .map(matcher -> matcher.group(1))
                .findFirst()
                .orElseThrow(() -> new AssertionError("Missing cookie " + name));
    }

    private String localOrigin() {
        return "http://localhost:" + port;
    }

    private record SessionCookies(String sessionCookie, String csrfToken) {
        String cookieHeader() {
            return sessionCookie + "; XSRF-TOKEN=" + csrfToken;
        }
    }

}
