package eu.royalblackwater.api.integration;

import static org.assertj.core.api.Assertions.assertThat;

import eu.royalblackwater.api.config.PrivacyRetentionProperties;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.privacy.PrivacyRetentionService;
import eu.royalblackwater.api.security.PasswordHasher;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
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
class PrivacyIntegrationTest {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16.4-alpine");

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        Path runtime = Path.of(System.getProperty("java.io.tmpdir"), "rbf-privacy-integration-test");
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("rbf.secrets.encryption-keys",
                () -> "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=");
        registry.add("rbf.bootstrap-admin.password", () -> "Privacy-Test-Admin-Password-42!");
        registry.add("rbf.session.secure", () -> false);
        registry.add("rbf.scheduling.enabled", () -> false);
        registry.add("rbf.storage.upload-root", () -> runtime.resolve("uploads").toString());
        registry.add("rbf.operations.control-root", () -> runtime.resolve("control").toString());
    }

    @Autowired JdbcQueryService jdbc;
    @Autowired PasswordHasher passwords;
    @LocalServerPort int port;

    @Test
    void cookieApiRejectsNecessaryOptOutAndPersistsOnlyOpaqueConsentKeys() throws Exception {
        assertStatus(get("/api/privacy/cookie-policy", null), 200);
        long before = jdbc.count("select count(*) from cookie_consent_decisions", Map.of());
        assertStatus(post("/api/privacy/cookie-consent",
                "{\"necessary\":false,\"analytics\":true}", null), 422);
        assertThat(jdbc.count("select count(*) from cookie_consent_decisions", Map.of())).isEqualTo(before);

        HttpResponse<String> saved = post("/api/privacy/cookie-consent",
                "{\"necessary\":true,\"preferences\":true,\"analytics\":false,\"external_media\":true}",
                null);
        assertStatus(saved, 200);
        assertThat(saved.body()).contains("\"has_decision\":true", "\"preferences\":true")
                .doesNotContain("consent_key");
        String setCookie = saved.headers().allValues("set-cookie").stream()
                .filter(value -> value.startsWith("rbf_cookie_consent="))
                .findFirst().orElseThrow();
        assertThat(setCookie).contains("HttpOnly", "SameSite=Lax", "Path=/").doesNotContain("Domain=");
        String consentCookie = cookie(saved, "rbf_cookie_consent");
        assertStatus(get("/api/privacy/cookie-consent", consentCookie), 200);
        assertThat(jdbc.count("select count(*) from cookie_consent_decisions where consent_key=:key",
                Map.of("key", consentCookie.substring(consentCookie.indexOf('=') + 1)))).isEqualTo(1);
    }

    @Test
    void correctionContactAndExportFlowsEnforceValidationAuthorizationAndSecretExclusions() throws Exception {
        String username = "privacy-member-" + System.nanoTime();
        createMember(username, "Privacy-Test-Member-Password-42!");
        SessionCookies member = login(username, "Privacy-Test-Member-Password-42!");
        SessionCookies administrator = login("admin", "Privacy-Test-Admin-Password-42!");

        HttpResponse<String> export = get("/api/privacy/data-export", member.sessionCookie());
        assertStatus(export, 200);
        assertThat(export.body()).contains("\"username\":\"" + username + "\"")
                .doesNotContain("password_hash", "token_hash", "consent_key");
        assertStatus(get("/api/admin/privacy-requests", member.sessionCookie()), 403);

        HttpResponse<String> request = post("/api/privacy/requests",
                "{\"request_type\":\"correction\",\"details\":\"Correct my stored profile data.\"}", member);
        assertStatus(request, 201);
        long requestId = jsonId(request.body());
        assertStatus(post("/api/privacy/requests",
                "{\"request_type\":\"correction\",\"details\":\"Duplicate request.\"}", member), 409);
        assertStatus(put("/api/admin/privacy-requests/" + requestId,
                "{\"decision\":\"complete\",\"resolution_note\":\"Correction confirmed.\"}", administrator), 200);

        String email = username + "@example.com";
        assertStatus(post("/api/privacy/contact", contactJson(email, "bot value"), null), 400);
        HttpResponse<String> contact = post("/api/privacy/contact", contactJson(email, ""), null);
        assertStatus(contact, 201);
        long contactId = jsonId(contact.body());
        assertStatus(put("/api/admin/privacy-requests/contacts/" + contactId,
                "{\"decision\":\"reject\",\"resolution_note\":\"No personal data included.\"}", administrator), 200);
        assertThat(jdbc.required("select status,reply_email from privacy_contact_requests where id=:id",
                Map.of("id", contactId))).containsEntry("status", "rejected").containsEntry("reply_email", email);
    }

    @Test
    void completedDeletionPseudonymizesTheAccountAndInvalidatesItsSession() throws Exception {
        String username = "delete-member-" + System.nanoTime();
        long userId = createMember(username, "Privacy-Delete-Member-Password-42!");
        SessionCookies member = login(username, "Privacy-Delete-Member-Password-42!");
        SessionCookies administrator = login("admin", "Privacy-Test-Admin-Password-42!");
        HttpResponse<String> request = post("/api/privacy/requests",
                "{\"request_type\":\"deletion\",\"confirmation\":\"" + username + "\"}", member);
        assertStatus(request, 201);

        assertStatus(put("/api/admin/privacy-requests/" + jsonId(request.body()),
                "{\"decision\":\"complete\",\"resolution_note\":\"Identity and consequences verified.\"}",
                administrator), 200);

        assertThat(jdbc.required("select username,is_active from users where id=:id", Map.of("id", userId)))
                .hasEntrySatisfying("username", value -> assertThat(value).asString().startsWith("deleted-"))
                .containsEntry("is_active", false);
        assertThat(jdbc.count("select count(*) from user_profiles where user_id=:id", Map.of("id", userId))).isZero();
        assertThat(jdbc.count("select count(*) from auth_sessions where user_id=:id", Map.of("id", userId))).isZero();
        assertStatus(get("/api/privacy/data-export", member.sessionCookie()), 401);
        assertStatus(post("/api/auth/login",
                "{\"username\":\"" + username + "\",\"password\":\"Privacy-Delete-Member-Password-42!\"}",
                null), 401);
    }

    @Test
    void retentionDeletesExpiredHistoryButPreservesPendingAndRecentRecords() {
        long userId = createMember("retention-member-" + System.nanoTime(), "Retention-Member-Password-42!");
        jdbc.update("""
                insert into cookie_consent_decisions(consent_key,user_id,policy_version,necessary,preferences,
                    analytics,external_media,created_at)
                values('abcdefghijklmnopqrstuvwxyz_OLDKEY-123456',:id,'old',true,false,false,false,current_timestamp-interval '401 days'),
                      ('abcdefghijklmnopqrstuvwxyz_NEWKEY-123456',:id,'current',true,false,false,false,current_timestamp)
                """, Map.of("id", userId));
        jdbc.update("""
                insert into data_subject_requests(subject_user_id,request_type,status,created_at,resolved_at)
                values(:id,'correction','completed',current_timestamp-interval '500 days',current_timestamp-interval '401 days'),
                      (:id,'correction','pending',current_timestamp-interval '500 days',null)
                """, Map.of("id", userId));
        jdbc.update("""
                insert into privacy_contact_requests(user_id,reply_email,subject,message,status,created_at,resolved_at)
                values(:id,'old@example.com','Old contact','Old privacy message','rejected',
                    current_timestamp-interval '500 days',current_timestamp-interval '401 days')
                """, Map.of("id", userId));

        PrivacyRetentionService.CleanupResult result = new PrivacyRetentionService(
                jdbc, new PrivacyRetentionProperties(
                        Duration.ofDays(400), Duration.ofDays(400), Duration.ofHours(24)), Clock.systemUTC())
                .cleanExpiredData();

        assertThat(result.consentDecisions()).isPositive();
        assertThat(result.subjectRequests()).isEqualTo(1);
        assertThat(result.contacts()).isEqualTo(1);
        assertThat(jdbc.count("select count(*) from cookie_consent_decisions where user_id=:id", Map.of("id", userId)))
                .isEqualTo(1);
        assertThat(jdbc.count("select count(*) from data_subject_requests where subject_user_id=:id", Map.of("id", userId)))
                .isEqualTo(1);
    }

    private String contactJson(String email, String website) {
        return "{\"reply_email\":\"" + email + "\",\"subject\":\"Privacy question\","
                + "\"message\":\"Please clarify how my data is processed.\",\"website\":\"" + website + "\"}";
    }

    private long createMember(String username, String password) {
        long id = jdbc.insertReturningId("""
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:password,(select id from site_roles where code='user'),true,false,current_timestamp,current_timestamp)
                returning id
                """, Map.of("username", username, "password", passwords.hash(password)));
        jdbc.update("""
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:id,'Privacy Test Member',current_timestamp,current_timestamp)
                """, Map.of("id", id));
        return id;
    }

    private SessionCookies login(String username, String password) throws Exception {
        HttpResponse<String> login = post("/api/auth/login",
                "{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}", null);
        assertStatus(login, 200);
        String session = cookie(login, "rbf_hub_session");
        HttpResponse<String> csrf = get("/api/auth/me", session);
        return new SessionCookies(session, cookieValue(csrf, "XSRF-TOKEN"));
    }

    private HttpResponse<String> get(String path, String cookie) throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(origin() + path)).GET();
        if (cookie != null) request.header("Cookie", cookie);
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> post(String path, String body, SessionCookies session) throws Exception {
        return send("POST", path, body, session);
    }

    private HttpResponse<String> put(String path, String body, SessionCookies session) throws Exception {
        return send("PUT", path, body, session);
    }

    private HttpResponse<String> send(String method, String path, String body, SessionCookies session) throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(origin() + path))
                .header("Content-Type", "application/json").header("Origin", origin())
                .method(method, HttpRequest.BodyPublishers.ofString(body));
        if (session != null) request.header("Cookie", session.cookieHeader()).header("X-XSRF-TOKEN", session.csrfToken());
        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private static String cookie(HttpResponse<String> response, String name) {
        return name + "=" + cookieValue(response, name);
    }

    private static String cookieValue(HttpResponse<String> response, String name) {
        Pattern pattern = Pattern.compile("(?:^|;\\s*)" + Pattern.quote(name) + "=([^;]+)");
        return response.headers().allValues("set-cookie").stream().map(pattern::matcher)
                .filter(java.util.regex.Matcher::find).map(matcher -> matcher.group(1)).findFirst().orElseThrow();
    }

    private static long jsonId(String body) {
        var matcher = Pattern.compile("\\\"id\\\":(\\d+)").matcher(body);
        if (!matcher.find()) throw new AssertionError("Missing id in response: " + body);
        return Long.parseLong(matcher.group(1));
    }

    private static void assertStatus(HttpResponse<String> response, int expected) {
        assertThat(response.statusCode()).as("response=%s", response.body()).isEqualTo(expected);
    }

    private String origin() {
        return "http://localhost:" + port;
    }

    private record SessionCookies(String sessionCookie, String csrfToken) {
        String cookieHeader() {
            return sessionCookie + "; XSRF-TOKEN=" + csrfToken;
        }
    }
}
