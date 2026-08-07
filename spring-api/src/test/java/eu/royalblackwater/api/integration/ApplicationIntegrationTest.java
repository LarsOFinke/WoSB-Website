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
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import static org.assertj.core.api.Assertions.assertThat;

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

    @Autowired
    BootstrapAdministratorInitializer bootstrapAdministrator;

    @Autowired
    ReferenceDataSeeder referenceDataSeeder;

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
    void bootstrapAdministratorCanLoginWithConfiguredFirstRunCredentials() throws Exception {
        HttpResponse<String> response = post(
                "/api/auth/login",
                "{\"username\":\"admin\",\"password\":\"Integration-Test-Admin-Password-42!\"}",
                null, null, localOrigin());

        assertStatus(response, 200, "POST", "/api/auth/login");
        assertThat(response.body()).contains("\"username\":\"admin\"");
        assertThat(response.headers().allValues("set-cookie"))
                .anyMatch(value -> value.startsWith("rbf_hub_session="));

        HttpResponse<String> rejected = post(
                "/api/auth/login",
                "{\"username\":\"admin\",\"password\":\"definitely-wrong-password\"}",
                null, null, localOrigin());
        assertStatus(rejected, 401, "POST", "/api/auth/login");
        assertThat(rejected.body()).contains("\"detail\":\"Invalid username or password.\"");
    }

    @Test
    void repairsBootstrapFleetLeadershipAndKeepsInitializationIdempotent() {
        Map<String, Object> membership = bootstrapMembership();
        assertThat(membership).containsEntry("status", "active").containsEntry("role", "fleet_admiral")
                .containsEntry("slug", "royal-blackwater-fleet")
                .containsEntry("can_manage_fleet", true).containsEntry("can_manage_members", true);

        jdbc.update("""
                update fleet_memberships set status='inactive',fleet_role_id=(select id from fleet_roles where code='member')
                where id=:id
                """, Map.of("id", ((Number) membership.get("id")).longValue()));
        bootstrapAdministrator.initialize();
        bootstrapAdministrator.initialize();

        assertThat(bootstrapMembership()).containsEntry("status", "active").containsEntry("role", "fleet_admiral");
        assertThat(jdbc.count("""
                select count(*) from fleet_memberships m join users u on u.id=m.user_id
                where u.is_bootstrap_admin=true
                """, Map.of())).isEqualTo(1);
    }

    @Test
    void preservesMasterDataOverridesDuringStartupSyncAndRestoresThemExplicitly() throws Exception {
        Map<String, Object> category = jdbc.required("""
                select id,label from build_item_categories where seed_key is not null order by id limit 1
                """, Map.of());
        long categoryId = ((Number) category.get("id")).longValue();
        String seedLabel = String.valueOf(category.get("label"));
        long categories = jdbc.count("select count(*) from build_item_categories", Map.of());
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        assertStatus(put("/api/admin/master-data/categories/" + categoryId,
                "{\"label\":\"Local integration override\",\"sort_order\":1,\"is_active\":true}",
                administrator), 200, "PUT", "/api/admin/master-data/categories/{category_id}");
        jdbc.update("update fleet_roles set can_manage_fleet=false where code='fleet_admiral'", Map.of());

        referenceDataSeeder.synchronize(false);
        assertThat(jdbc.required("select label,is_seed_overridden from build_item_categories where id=:id",
                Map.of("id", categoryId))).containsEntry("label", "Local integration override")
                .containsEntry("is_seed_overridden", true);
        assertThat(jdbc.required("select can_manage_fleet from fleet_roles where code='fleet_admiral'", Map.of()))
                .containsEntry("can_manage_fleet", true);
        assertThat(jdbc.count("select count(*) from build_item_categories", Map.of())).isEqualTo(categories);

        assertStatus(post("/api/admin/master-data/categories/" + categoryId + "/restore-seed", "",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin()),
                200, "POST", "/api/admin/master-data/categories/{category_id}/restore-seed");
        assertThat(jdbc.required("select label,is_seed_overridden from build_item_categories where id=:id",
                Map.of("id", categoryId))).containsEntry("label", seedLabel).containsEntry("is_seed_overridden", false);
        assertThat(jdbc.count("select count(*) from build_item_categories", Map.of())).isEqualTo(categories);
    }

    @Test
    void bootstrapAdministratorCanLoadFleetManagementWorkspace() throws Exception {
        referenceDataSeeder.synchronize(false);
        bootstrapAdministrator.initialize();
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");

        HttpResponse<String> manageable = get("/api/fleets/manageable", administrator.sessionCookie());
        assertStatus(manageable, 200, "GET", "/api/fleets/manageable");
        long fleetId = jsonId(manageable.body());

        HttpResponse<String> detail = get("/api/fleets/" + fleetId + "/manage", administrator.sessionCookie());
        assertStatus(detail, 200, "GET", "/api/fleets/{fleet_id}/manage");
        assertThat(detail.body()).contains("\"memberships\":[", "\"management\":{");
        assertThat(detail.body()).contains("\"protected\":");
        assertThat(detail.body()).doesNotContain("\"protected_value\":");

        HttpResponse<String> roles = get(
                "/api/fleets/" + fleetId + "/roles?include_inactive=true", administrator.sessionCookie());
        assertStatus(roles, 200, "GET", "/api/fleets/{fleet_id}/roles?include_inactive=true");
        assertThat(roles.body()).contains("\"code\":\"fleet_admiral\"");
    }

    @Test
    void bootstrapFleetManagerCanCreateAndOperateASquadOverHttp() throws Exception {
        SessionCookies administrator = login("admin", "Integration-Test-Admin-Password-42!");
        long membershipId = ((Number) bootstrapMembership().get("id")).longValue();
        String squadName = "Integration Squadron " + System.nanoTime();
        HttpResponse<String> created = post("/api/squads", "{\"name\":\"" + squadName
                        + "\",\"leader_membership_id\":" + membershipId + ",\"max_members\":8}",
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(created, 201, "POST", "/api/squads");
        long squadId = jsonId(created.body());

        assertStatus(get("/api/squads/" + squadId, administrator.sessionCookie()),
                200, "GET", "/api/squads/{squad_id}");
        assertStatus(get("/api/squads/mine", administrator.sessionCookie()), 200, "GET", "/api/squads/mine");
        HttpResponse<String> roster = get("/api/squads/roster", administrator.sessionCookie());
        assertStatus(roster, 200, "GET", "/api/squads/roster");
        assertThat(roster.body()).contains("\"fleet_membership_id\":" + membershipId);

        HttpResponse<String> archived = delete("/api/squads/" + squadId,
                administrator.cookieHeader(), administrator.csrfToken(), localOrigin());
        assertStatus(archived, 204, "DELETE", "/api/squads/{squad_id}");
        assertThat(jdbc.count("select count(*) from squads where id=:id and is_active=false", Map.of("id", squadId)))
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
        assertStatus(fleet, 200, "GET", "/api/fleets/public/official");
        assertThat(fleet.body()).contains("\"slug\":\"royal-blackwater-fleet\"")
                .contains("\"role\":\"fleet_admiral\"");

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
        assertThat(response.body()).contains("\"detail\":");
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
            assertStatus(get(path, administrator.sessionCookie()), 200, "GET", path);
        }

        HttpResponse<String> calendar = get(
                "/api/calendar/events?start=2030-01-01T00:00:00.000Z&end=2030-02-01T00:00:00.000Z",
                administrator.sessionCookie());
        assertStatus(calendar, 200, "GET", "/api/calendar/events");

        HttpResponse<String> invalidCalendar = get(
                "/api/calendar/events?start=not-a-timestamp", administrator.sessionCookie());
        assertStatus(invalidCalendar, 400, "GET", "/api/calendar/events?start=not-a-timestamp");
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
            assertStatus(get(path, administrator.sessionCookie()), 200, "GET", path);
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

    private HttpResponse<String> delete(String path, String cookie, String csrf, String origin) throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(localOrigin() + path))
                .header("Origin", origin).DELETE();
        if (cookie != null) request.header("Cookie", cookie);
        if (csrf != null) request.header("X-XSRF-TOKEN", csrf);
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> put(String path, String body, SessionCookies session) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create(localOrigin() + path)).header("Content-Type", "application/json")
                .header("Origin", localOrigin()).header("Cookie", session.cookieHeader())
                .header("X-XSRF-TOKEN", session.csrfToken()).PUT(HttpRequest.BodyPublishers.ofString(body)).build();
        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
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

    private static void assertStatus(
            HttpResponse<String> response, int expectedStatus, String method, String path) {
        String body = response.body() == null ? "" : response.body().replaceAll("[\\r\\n\\t]+", " ");
        String excerpt = body.substring(0, Math.min(body.length(), 500));
        assertThat(response.statusCode())
                .as("%s %s expected status %s but received %s; response=%s",
                        method, path, expectedStatus, response.statusCode(), excerpt)
                .isEqualTo(expectedStatus);
    }

    private Map<String, Object> bootstrapMembership() {
        return jdbc.required("""
                select m.id,m.status,r.code role,r.can_manage_fleet,r.can_manage_members,f.slug
                from users u join fleet_memberships m on m.user_id=u.id
                join fleet_roles r on r.id=m.fleet_role_id join fleets f on f.id=m.fleet_id
                where u.is_bootstrap_admin=true
                """, Map.of());
    }

    private static long jsonId(String body) {
        var matcher = Pattern.compile("\\\"id\\\":(\\d+)").matcher(body);
        if (!matcher.find()) throw new AssertionError("Response does not contain a numeric id: " + body);
        return Long.parseLong(matcher.group(1));
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
