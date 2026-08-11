package eu.royalblackwater.api.integration;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.io.ByteArrayOutputStream;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Map;
import java.util.UUID;
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
import static org.assertj.core.api.Assertions.assertThatCode;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers(disabledWithoutDocker = true)
class BuildPrintoutIntegrationTest {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = PostgresTestContainerFactory.create();

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        Path runtime = Path.of(System.getProperty("java.io.tmpdir"), "rbf-printout-integration-test");
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("rbf.secrets.encryption-keys",
                () -> "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=");
        registry.add("rbf.bootstrap-admin.password", () -> "Integration-Test-Admin-Password-42!");
        registry.add("rbf.session.secure", () -> false);
        registry.add("rbf.scheduling.enabled", () -> false);
        registry.add("rbf.diagnostics.http-lifecycle-logging", () -> true);
        registry.add("rbf.storage.upload-root", () -> runtime.resolve("uploads").toString());
        registry.add("rbf.operations.control-root", () -> runtime.resolve("control").toString());
    }

    @Autowired
    JdbcQueryService jdbc;

    @LocalServerPort
    int port;

    @Test
    void reusesAndInvalidatesVersionedBuildPrintoutsAcrossHttpAndDatabaseBoundaries() throws Exception {
        Session session = login();
        Map<String, Object> ship = jdbc.required(
                "select id,sailor_minimum from ships where is_active=true order by id limit 1", Map.of());
        long shipId = ((Number) ship.get("id")).longValue();
        long sailors = ((Number) ship.get("sailor_minimum")).longValue();
        long nonce = Math.abs(System.nanoTime());

        HttpResponse<String> created = jsonRequest("POST", "/api/builds",
                "{\"build_name\":\"Printout integration " + nonce + "\",\"ship_id\":" + shipId
                        + ",\"sailors\":" + sailors + "}", session);
        assertThat(created.statusCode()).isEqualTo(201);
        long buildId = jsonLong(created.body(), "id");
        String sourceVersion = jsonString(created.body(), "updated_at");
        String firstCacheKey = "integration-v1:" + "a".repeat(64);

        HttpResponse<String> first = putPrintout(buildId, firstCacheKey, sourceVersion, session);
        assertThat(first.statusCode()).isEqualTo(200);
        assertThat(first.body()).contains("\"changed\":true", "\"cache_key\":\"" + firstCacheKey + "\"");
        assertRequestId(first);

        HttpResponse<byte[]> downloaded = getPrintout(buildId, firstCacheKey, session);
        assertThat(downloaded.statusCode()).isEqualTo(200);
        assertThat(downloaded.body()).startsWith((byte) 0x89, (byte) 0x50, (byte) 0x4e, (byte) 0x47);
        java.awt.image.BufferedImage downloadedImage = javax.imageio.ImageIO.read(
                new java.io.ByteArrayInputStream(downloaded.body()));
        assertThat(downloadedImage.getWidth()).isEqualTo(64);
        assertThat(downloadedImage.getHeight()).isEqualTo(64);
        assertRequestId(downloaded);

        HttpResponse<String> reused = putPrintout(buildId, firstCacheKey, sourceVersion, session);
        assertThat(reused.statusCode()).isEqualTo(200);
        assertThat(reused.body()).contains("\"changed\":false");
        assertThat(jdbc.count("select count(*) from audit_logs where entity_type='build' and entity_id=:id "
                + "and action='printout_update'", Map.of("id", String.valueOf(buildId)))).isEqualTo(1);

        HttpResponse<String> updated = jsonRequest("PUT", "/api/builds/mine/" + buildId,
                "{\"build_name\":\"Printout integration updated " + nonce + "\",\"ship_id\":" + shipId
                        + ",\"sailors\":" + sailors + "}", session);
        assertThat(updated.statusCode()).isEqualTo(200);
        String nextSourceVersion = jsonString(updated.body(), "updated_at");

        HttpResponse<byte[]> stale = getPrintout(buildId, firstCacheKey, session);
        assertThat(stale.statusCode()).isEqualTo(404);
        assertThat(jdbc.required("select printout_cache_key,printout_checksum,printout_source_updated_at "
                + "from builds where id=:id", Map.of("id", buildId)))
                .containsEntry("printout_cache_key", null)
                .containsEntry("printout_checksum", null)
                .containsEntry("printout_source_updated_at", null);

        String secondCacheKey = "integration-v2:" + "b".repeat(64);
        HttpResponse<String> regenerated = putPrintout(buildId, secondCacheKey, nextSourceVersion, session);
        assertThat(regenerated.statusCode()).isEqualTo(200);
        assertThat(regenerated.body()).contains("\"changed\":true", "\"cache_key\":\"" + secondCacheKey + "\"");
        assertThat(getPrintout(buildId, secondCacheKey, session).statusCode()).isEqualTo(200);
    }

    private Session login() throws Exception {
        HttpRequest login = HttpRequest.newBuilder(uri("/api/auth/login"))
                .header("Content-Type", "application/json")
                .header("Origin", origin())
                .POST(HttpRequest.BodyPublishers.ofString(
                        "{\"username\":\"admin\",\"password\":\"Integration-Test-Admin-Password-42!\"}"))
                .build();
        HttpResponse<String> loginResponse = client().send(login, HttpResponse.BodyHandlers.ofString());
        assertThat(loginResponse.statusCode()).isEqualTo(200);
        String sessionCookie = cookie(loginResponse, "rbf_hub_session");
        HttpRequest csrf = HttpRequest.newBuilder(uri("/api/auth/me")).header("Cookie", sessionCookie).GET().build();
        HttpResponse<String> csrfResponse = client().send(csrf, HttpResponse.BodyHandlers.ofString());
        String csrfCookie = cookie(csrfResponse, "XSRF-TOKEN");
        return new Session(sessionCookie + "; " + csrfCookie, csrfCookie.substring("XSRF-TOKEN=".length()));
    }

    private HttpResponse<String> jsonRequest(String method, String path, String body, Session session) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(uri(path))
                .header("Content-Type", "application/json")
                .header("Origin", origin())
                .header("Cookie", session.cookieHeader())
                .header("X-XSRF-TOKEN", session.csrfToken())
                .method(method, HttpRequest.BodyPublishers.ofString(body))
                .build();
        return client().send(request, HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> putPrintout(
            long buildId, String cacheKey, String sourceUpdatedAt, Session session) throws Exception {
        String boundary = "----rbf-integration-" + UUID.randomUUID();
        ByteArrayOutputStream body = new ByteArrayOutputStream();
        body.write(("--" + boundary + "\r\n"
                + "Content-Disposition: form-data; name=\"image\"; filename=\"build.png\"\r\n"
                + "Content-Type: image/png\r\n\r\n").getBytes(StandardCharsets.UTF_8));
        body.write(pngBytes());
        body.write(("\r\n--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
        String path = "/api/builds/" + buildId + "/printout?cache_key=" + encode(cacheKey)
                + "&source_updated_at=" + encode(sourceUpdatedAt);
        HttpRequest request = HttpRequest.newBuilder(uri(path))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .header("Origin", origin())
                .header("Cookie", session.cookieHeader())
                .header("X-XSRF-TOKEN", session.csrfToken())
                .PUT(HttpRequest.BodyPublishers.ofByteArray(body.toByteArray()))
                .build();
        return client().send(request, HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<byte[]> getPrintout(long buildId, String cacheKey, Session session) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(uri(
                        "/api/builds/" + buildId + "/printout?cache_key=" + encode(cacheKey)))
                .header("Cookie", session.cookieHeader()).GET().build();
        return client().send(request, HttpResponse.BodyHandlers.ofByteArray());
    }

    private static byte[] pngBytes() {
        try {
            java.awt.image.BufferedImage image = new java.awt.image.BufferedImage(64, 64,
                    java.awt.image.BufferedImage.TYPE_INT_ARGB);
            for (int y = 0; y < image.getHeight(); y++) for (int x = 0; x < image.getWidth(); x++) {
                image.setRGB(x, y, new java.awt.Color(x * 4, y * 4, (x + y) * 2, 255).getRGB());
            }
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            javax.imageio.ImageIO.write(image, "png", output);
            return output.toByteArray();
        } catch (java.io.IOException exception) {
            throw new IllegalStateException(exception);
        }
    }

    private static String jsonString(String body, String name) {
        var matcher = Pattern.compile("\\\"" + Pattern.quote(name) + "\\\":\\\"([^\\\"]+)\\\"").matcher(body);
        assertThat(matcher.find()).as("JSON property %s in %s", name, body).isTrue();
        return matcher.group(1);
    }

    private static long jsonLong(String body, String name) {
        var matcher = Pattern.compile("\\\"" + Pattern.quote(name) + "\\\":(\\d+)").matcher(body);
        assertThat(matcher.find()).as("JSON property %s in %s", name, body).isTrue();
        return Long.parseLong(matcher.group(1));
    }

    private static void assertRequestId(HttpResponse<?> response) {
        String value = response.headers().firstValue("X-Request-Id").orElseThrow();
        assertThatCode(() -> UUID.fromString(value)).doesNotThrowAnyException();
    }

    private static String cookie(HttpResponse<?> response, String name) {
        Pattern pattern = Pattern.compile("(?:^|;\\s*)" + Pattern.quote(name) + "=([^;]+)");
        return response.headers().allValues("set-cookie").stream()
                .map(pattern::matcher).filter(java.util.regex.Matcher::find)
                .map(matcher -> name + "=" + matcher.group(1)).findFirst().orElseThrow();
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    private HttpClient client() { return HttpClient.newHttpClient(); }
    private URI uri(String path) { return URI.create(origin() + path); }
    private String origin() { return "http://localhost:" + port; }

    private record Session(String cookieHeader, String csrfToken) { }
}
