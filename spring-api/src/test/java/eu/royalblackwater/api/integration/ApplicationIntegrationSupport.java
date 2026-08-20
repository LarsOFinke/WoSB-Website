package eu.royalblackwater.api.integration;

import eu.royalblackwater.api.account.service.BootstrapAdministratorInitializer;
import eu.royalblackwater.api.masterdata.service.ReferenceDataSeeder;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.service.PasswordHasher;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.util.Map;
import java.util.regex.Pattern;
import org.flywaydb.core.Flyway;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;

import static org.assertj.core.api.Assertions.assertThat;

abstract class ApplicationIntegrationSupport {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = PostgresTestContainerFactory.create();

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        Flyway.configure()
                .dataSource(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword())
                .cleanDisabled(true)
                .validateMigrationNaming(true)
                .load()
                .migrate();
        Path runtime = Path.of(System.getProperty("java.io.tmpdir"), "rbf-integration-test");
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("spring.flyway.enabled", () -> false);
        registry.add("rbf.secrets.encryption-keys",
                () -> "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=");
        registry.add("rbf.bootstrap-admin.password", () -> "Integration-Test-Admin-Password-42!");
        registry.add("rbf.session.secure", () -> false);
        registry.add("rbf.scheduling.enabled", () -> false);
        registry.add("rbf.diagnostics.http-lifecycle-logging", () -> true);
        registry.add("rbf.storage.upload-root", () -> runtime.resolve("uploads").toString());
        registry.add("rbf.operations.control-root", () -> runtime.resolve("control").toString());
    }

    @Autowired JdbcQueryService jdbc;
    @Autowired PasswordHasher passwords;
    @Autowired BootstrapAdministratorInitializer bootstrapAdministrator;
    @Autowired ReferenceDataSeeder referenceDataSeeder;
    @LocalServerPort int port;

    HttpResponse<String> submitPublicRegistration(
            String username, String password, String displayName, boolean wantsFleetMembership,
            Long fleetId, String fleetApplicationNote) throws Exception {
        HttpResponse<String> csrfBootstrap = get("/api/auth/me");
        String xsrf = cookieValue(csrfBootstrap, "XSRF-TOKEN");
        String fleet = fleetId == null ? "null" : String.valueOf(fleetId);
        String note = fleetApplicationNote == null
                ? "null"
                : "\"" + fleetApplicationNote.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
        String body = "{\"username\":\"" + username + "\",\"password\":\"" + password
                + "\",\"display_name\":\"" + displayName + "\",\"wants_fleet_membership\":"
                + wantsFleetMembership + ",\"fleet_id\":" + fleet + ",\"fleet_application_note\":" + note + "}";
        HttpRequest request = HttpRequest.newBuilder(URI.create(localOrigin() + "/api/auth/register"))
                .header("Content-Type", "application/json")
                .header("Origin", localOrigin())
                .header("Cookie", "XSRF-TOKEN=" + xsrf)
                .header("X-XSRF-TOKEN", xsrf)
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
    }

    HttpResponse<String> get(String path) throws Exception { return get(path, null); }

    HttpResponse<String> get(String path, String cookie) throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(localOrigin() + path)).GET();
        if (cookie != null) request.header("Cookie", cookie);
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    HttpResponse<String> post(String path, String body, String cookie, String csrf, String origin)
            throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(localOrigin() + path))
                .header("Content-Type", "application/json")
                .header("Origin", origin)
                .POST(HttpRequest.BodyPublishers.ofString(body));
        if (cookie != null) request.header("Cookie", cookie);
        if (csrf != null) request.header("X-XSRF-TOKEN", csrf);
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    HttpResponse<String> delete(String path, String cookie, String csrf, String origin) throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(localOrigin() + path))
                .header("Origin", origin).DELETE();
        if (cookie != null) request.header("Cookie", cookie);
        if (csrf != null) request.header("X-XSRF-TOKEN", csrf);
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    HttpResponse<String> put(String path, String body, SessionCookies session) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create(localOrigin() + path))
                .header("Content-Type", "application/json")
                .header("Origin", localOrigin()).header("Cookie", session.cookieHeader())
                .header("X-XSRF-TOKEN", session.csrfToken())
                .PUT(HttpRequest.BodyPublishers.ofString(body)).build();
        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
    }

    SessionCookies login(String username, String password) throws Exception {
        HttpResponse<String> login = post("/api/auth/login",
                "{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}",
                null, null, localOrigin());
        assertThat(login.statusCode()).isEqualTo(200);
        String sessionCookie = cookie(login, "rbf_hub_session");
        HttpResponse<String> csrfBootstrap = get("/api/auth/me", sessionCookie);
        return new SessionCookies(sessionCookie, cookieValue(csrfBootstrap, "XSRF-TOKEN"));
    }

    void createMember(String username, String password) { createUser(username, password, "user"); }

    void createUser(String username, String password, String role) {
        jdbc.update("delete from users where username=:username", Map.of("username", username));
        long userId = jdbc.insertReturningId("""
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:password,(select id from site_roles where code=:role),true,false,current_timestamp,current_timestamp)
                returning id
                """, Map.of("username", username, "password", passwords.hash(password), "role", role));
        jdbc.update("""
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,'Integration Member',current_timestamp,current_timestamp)
                """, Map.of("userId", userId));
    }

    static String cookie(HttpResponse<String> response, String name) {
        return name + "=" + cookieValue(response, name);
    }

    static String cookieValue(HttpResponse<String> response, String name) {
        Pattern pattern = Pattern.compile("(?:^|;\\s*)" + Pattern.quote(name) + "=([^;]+)");
        return response.headers().allValues("set-cookie").stream()
                .map(pattern::matcher).filter(java.util.regex.Matcher::find)
                .map(matcher -> matcher.group(1)).findFirst()
                .orElseThrow(() -> new AssertionError("Missing cookie " + name));
    }

    static void assertStatus(HttpResponse<String> response, int expectedStatus, String method, String path) {
        String body = response.body() == null ? "" : response.body().replaceAll("[\\r\\n\\t]+", " ");
        String excerpt = body.substring(0, Math.min(body.length(), 500));
        assertThat(response.statusCode())
                .as("%s %s expected status %s but received %s; response=%s",
                        method, path, expectedStatus, response.statusCode(), excerpt)
                .isEqualTo(expectedStatus);
    }

    Map<String, Object> bootstrapMembership() {
        return jdbc.required("""
                select m.id,m.fleet_id,m.status,r.code role,r.can_manage_fleet,r.can_manage_members,f.slug
                from users u join fleet_memberships m on m.user_id=u.id
                join fleet_roles r on r.id=m.fleet_role_id join fleets f on f.id=m.fleet_id
                where u.is_bootstrap_admin=true
                """, Map.of());
    }

    static long jsonId(String body) {
        return jsonLong(body, "id");
    }

    static long jsonLong(String body, String field) {
        var matcher = Pattern.compile("\\\"" + Pattern.quote(field) + "\\\":(\\d+)").matcher(body);
        if (!matcher.find()) throw new AssertionError("Response does not contain numeric field " + field + ": " + body);
        return Long.parseLong(matcher.group(1));
    }

    String localOrigin() { return "http://localhost:" + port; }

    record SessionCookies(String sessionCookie, String csrfToken) {
        String cookieHeader() { return sessionCookie + "; XSRF-TOKEN=" + csrfToken; }
    }
}
