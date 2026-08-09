package eu.royalblackwater.api.integration;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import tools.jackson.databind.ObjectMapper;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers(disabledWithoutDocker = true)
class ApiSurfaceIntegrationTest {
    private static final String ADMIN_PASSWORD = "Api-Surface-Admin-Password-42!";
    private static final int SENTINEL_ID = 2_000_000_000;
    private static final Pattern COOKIE_VALUE = Pattern.compile("(?:^|;\\s*)%s=([^;]+)");
    private static final Pattern SIMPLE_ALTERNATION = Pattern.compile("^\\^\\(([^)]+)\\)\\$$");
    private static final List<String> HTTP_METHODS = List.of("get", "post", "put", "delete", "patch");

    @Container
    static final PostgreSQLContainer<?> POSTGRES = PostgresTestContainerFactory.create();

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        Path runtime = Path.of(System.getProperty("java.io.tmpdir"), "rbf-api-surface-integration-test");
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("rbf.secrets.encryption-keys",
                () -> "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=");
        registry.add("rbf.bootstrap-admin.password", () -> ADMIN_PASSWORD);
        registry.add("rbf.session.secure", () -> false);
        registry.add("rbf.scheduling.enabled", () -> false);
        registry.add("rbf.diagnostics.http-lifecycle-logging", () -> true);
        registry.add("rbf.storage.upload-root", () -> runtime.resolve("uploads").toString());
        registry.add("rbf.operations.control-root", () -> runtime.resolve("control").toString());
    }

    @Autowired
    JdbcQueryService jdbc;

    @Autowired
    ObjectMapper json;

    @LocalServerPort
    int port;

    private final HttpClient http = HttpClient.newHttpClient();

    @TestFactory
    Stream<DynamicTest> everyReadOperationAvoidsServerErrorsAcrossQueryBranches() throws Exception {
        SessionCookies administrator = login();
        ensureReadFixtures();
        List<DynamicTest> tests = new ArrayList<>();
        for (ContractOperation operation : contractOperations()) {
            if (!"GET".equals(operation.method())) continue;
            String minimal = requestPath(operation, false);
            tests.add(DynamicTest.dynamicTest("minimal GET " + operation.template(),
                    () -> assertNoServerError(send("GET", minimal, null, administrator, true), operation.method(), minimal)));
            if (hasOptionalQueryParameters(operation)) {
                String filtered = requestPath(operation, true);
                tests.add(DynamicTest.dynamicTest("filtered GET " + operation.template(),
                        () -> assertNoServerError(send("GET", filtered, null, administrator, true), operation.method(), filtered)));
            }
        }
        assertThat(tests).as("contract GET smoke cases").hasSizeGreaterThanOrEqualTo(70);
        return tests.stream();
    }

    @TestFactory
    Stream<DynamicTest> everyWriteOperationAvoidsServerErrorsAtTheTransportBoundary() throws Exception {
        SessionCookies administrator = login();
        List<DynamicTest> tests = new ArrayList<>();
        for (ContractOperation operation : contractOperations()) {
            if ("GET".equals(operation.method())) continue;
            String path = requestPath(operation, false);
            String mediaType = requestBodyMediaType(operation);
            boolean hasBody = mediaType != null;
            tests.add(DynamicTest.dynamicTest(operation.method() + " " + operation.template(), () -> {
                SessionCookies session = hasBody ? administrator : null;
                HttpResponse<String> response = "multipart/form-data".equals(mediaType)
                        ? sendEmptyMultipart(operation.method(), path, session)
                        : send(operation.method(), path, hasBody ? "{" : null, session, hasBody);
                assertNoServerError(response, operation.method(), path);
            }));
        }
        assertThat(tests).as("contract write smoke cases").hasSize(107);
        return tests.stream();
    }

    @TestFactory
    Stream<DynamicTest> everyContractOperationEnforcesItsAnonymousSecurityBoundary() throws Exception {
        SessionCookies anonymousCsrf = anonymousCsrf();
        List<DynamicTest> tests = new ArrayList<>();
        for (ContractOperation operation : contractOperations()) {
            String path = requestPath(operation, false);
            tests.add(DynamicTest.dynamicTest("anonymous " + operation.method() + " " + operation.template(), () -> {
                String mediaType = requestBodyMediaType(operation);
                SessionCookies csrf = "GET".equals(operation.method()) ? null : anonymousCsrf;
                HttpResponse<String> response = "multipart/form-data".equals(mediaType)
                        ? sendEmptyMultipart(operation.method(), path, csrf)
                        : send(operation.method(), path, mediaType == null ? null : "{", csrf, true);
                if (isPublicOperation(operation)) {
                    assertThat(response.statusCode())
                            .as("public %s %s must remain anonymously reachable; response=%s",
                                    operation.method(), path, excerpt(response.body()))
                            .isNotIn(401, 403);
                } else {
                    assertThat(response.statusCode())
                            .as("protected %s %s must reject anonymous access after CSRF has been satisfied; response=%s",
                                    operation.method(), path, excerpt(response.body()))
                            .isEqualTo(401);
                }
            }));
        }
        assertThat(tests).as("anonymous security cases").hasSize(177);
        return tests.stream();
    }

    @TestFactory
    Stream<DynamicTest> everyAuthenticatedWriteRequiresCsrf() throws Exception {
        SessionCookies administrator = login();
        List<DynamicTest> tests = new ArrayList<>();
        for (ContractOperation operation : contractOperations()) {
            if ("GET".equals(operation.method()) || isCsrfBootstrapOperation(operation)) continue;
            String path = requestPath(operation, false);
            tests.add(DynamicTest.dynamicTest("missing CSRF " + operation.method() + " " + operation.template(), () -> {
                String mediaType = requestBodyMediaType(operation);
                HttpResponse<String> response = "multipart/form-data".equals(mediaType)
                        ? sendEmptyMultipartWithoutCsrf(operation.method(), path, administrator)
                        : sendWithoutCsrf(operation.method(), path, mediaType == null ? null : "{}", administrator);
                assertThat(response.statusCode())
                        .as("authenticated write without CSRF must be rejected: %s %s response=%s",
                                operation.method(), path, excerpt(response.body()))
                        .isEqualTo(403);
            }));
        }
        assertThat(tests).as("authenticated CSRF boundary cases").isNotEmpty();
        return tests.stream();
    }

    @TestFactory
    Stream<DynamicTest> multipartOperationsRejectWrongContentTypesWithoutServerErrors() throws Exception {
        SessionCookies administrator = login();
        List<DynamicTest> tests = new ArrayList<>();
        for (ContractOperation operation : contractOperations()) {
            if (!"multipart/form-data".equals(requestBodyMediaType(operation))) continue;
            String path = requestPath(operation, false);
            tests.add(DynamicTest.dynamicTest("wrong content type " + operation.method() + " " + operation.template(), () -> {
                HttpResponse<String> response = send(operation.method(), path, "{", administrator, true);
                assertThat(response.statusCode())
                        .as("%s %s should reject JSON for multipart; response=%s", operation.method(), path, excerpt(response.body()))
                        .isEqualTo(415);
            }));
        }
        assertThat(tests).as("multipart wrong-content-type cases").hasSize(2);
        return tests.stream();
    }

    @TestFactory
    Stream<DynamicTest> contractOperationInventoryRemainsFullyRepresented() throws Exception {
        List<ContractOperation> operations = contractOperations();
        long reads = operations.stream().filter(operation -> "GET".equals(operation.method())).count();
        long writes = operations.size() - reads;
        return Stream.of(
                DynamicTest.dynamicTest("177 contract operations", () -> assertThat(operations).hasSize(177)),
                DynamicTest.dynamicTest("70 GET operations", () -> assertThat(reads).isEqualTo(70)),
                DynamicTest.dynamicTest("107 write operations", () -> assertThat(writes).isEqualTo(107)));
    }

    private List<ContractOperation> contractOperations() throws Exception {
        Map<String, Object> contract = readContract();
        Map<String, Object> paths = map(contract.get("paths"));
        List<ContractOperation> result = new ArrayList<>();
        for (Map.Entry<String, Object> pathEntry : paths.entrySet()) {
            Map<String, Object> pathItem = map(pathEntry.getValue());
            for (String method : HTTP_METHODS) {
                Object rawOperation = pathItem.get(method);
                if (rawOperation instanceof Map<?, ?>) {
                    result.add(new ContractOperation(method.toUpperCase(Locale.ROOT), pathEntry.getKey(), pathItem,
                            map(rawOperation)));
                }
            }
        }
        return List.copyOf(result);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> readContract() throws Exception {
        Path contract = Stream.of(
                        Path.of(System.getProperty("user.dir"), "..", "openapi", "openapi.json"),
                        Path.of(System.getProperty("user.dir"), "openapi", "openapi.json"))
                .map(Path::normalize)
                .filter(Files::isRegularFile)
                .findFirst()
                .orElseThrow(() -> new AssertionError("Could not locate openapi/openapi.json from "
                        + System.getProperty("user.dir")));
        return json.readValue(Files.readString(contract), Map.class);
    }

    private String requestPath(ContractOperation operation, boolean includeOptionalQuery) {
        String path = operation.template();
        List<Map<String, Object>> parameters = parameters(operation);
        for (Map<String, Object> parameter : parameters) {
            if (!"path".equals(parameter.get("in"))) continue;
            String name = String.valueOf(parameter.get("name"));
            path = path.replace("{" + name + "}", encode(pathValue(name)));
        }

        List<String> query = new ArrayList<>();
        for (Map<String, Object> parameter : parameters) {
            if (!"query".equals(parameter.get("in"))) continue;
            boolean required = Boolean.TRUE.equals(parameter.get("required"));
            if (!required && !includeOptionalQuery) continue;
            String name = String.valueOf(parameter.get("name"));
            query.add(encode(name) + "=" + encode(queryValue(operation, name, map(parameter.get("schema")))));
        }
        return query.isEmpty() ? path : path + "?" + String.join("&", query);
    }

    private String requestBodyMediaType(ContractOperation operation) {
        Map<String, Object> requestBody = map(operation.operation().get("requestBody"));
        Map<String, Object> content = map(requestBody.get("content"));
        if (content.containsKey("multipart/form-data")) return "multipart/form-data";
        if (content.containsKey("application/json")) return "application/json";
        return content.isEmpty() ? null : content.keySet().iterator().next();
    }

    private List<Map<String, Object>> parameters(ContractOperation operation) {
        List<Map<String, Object>> result = new ArrayList<>();
        addParameters(result, operation.pathItem().get("parameters"));
        addParameters(result, operation.operation().get("parameters"));
        return result;
    }

    private void addParameters(List<Map<String, Object>> target, Object raw) {
        if (!(raw instanceof List<?> values)) return;
        for (Object value : values) {
            if (value instanceof Map<?, ?>) target.add(map(value));
        }
    }

    private boolean hasOptionalQueryParameters(ContractOperation operation) {
        return parameters(operation).stream().anyMatch(parameter -> "query".equals(parameter.get("in"))
                && !Boolean.TRUE.equals(parameter.get("required")));
    }

    private String pathValue(String name) {
        return switch (name) {
            case "fleet_id" -> valueOf("""
                    select m.fleet_id result_value from users u join fleet_memberships m on m.user_id=u.id
                    where u.is_bootstrap_admin=true
                    """);
            case "membership_id" -> valueOf("""
                    select m.id result_value from users u join fleet_memberships m on m.user_id=u.id
                    where u.is_bootstrap_admin=true
                    """);
            case "user_id" -> valueOf("select id result_value from users where is_bootstrap_admin=true");
            case "role_id" -> valueOf("select id result_value from fleet_roles where code='member'");
            case "ship_id" -> valueOf("select id result_value from ships where is_active=true order by id limit 1");
            case "category_id" -> valueOf("select id result_value from build_item_categories order by id limit 1");
            case "option_id" -> valueOf("select id result_value from build_item_options order by id limit 1");
            case "build_id" -> String.valueOf(surfaceBuildId());
            case "slug" -> String.valueOf(jdbc.required(
                    "select slug from build_roles order by sort_order,slug limit 1", Map.of()).get("slug"));
            default -> String.valueOf(SENTINEL_ID);
        };
    }

    private String valueOf(String sql) {
        return String.valueOf(jdbc.required(sql, Map.of()).get("result_value"));
    }

    private void ensureReadFixtures() {
        if (jdbc.count("select count(*) from registration_requests where username='surface-pending-review'", Map.of()) == 0) {
            jdbc.update("""
                    insert into registration_requests(username,password_hash,display_name,wants_fleet_membership,status,created_at,updated_at)
                    values('surface-pending-review','!surface-only!','Surface Pending Review',false,'pending',current_timestamp,current_timestamp)
                    """, Map.of());
        }
        surfaceBuildId();
    }

    private long surfaceBuildId() {
        var existing = jdbc.optional("select id from builds where build_name='Surface Contract Build' order by id limit 1", Map.of());
        if (existing.isPresent()) return ((Number) existing.get().get("id")).longValue();
        Map<String, Object> ship = jdbc.required("select id,sailor_minimum from ships where is_active=true order by id limit 1", Map.of());
        return jdbc.insertReturningId("""
                insert into builds(build_name,build_type,ship_id,owner_id,is_official_template,
                    mortar_modification_installed,sailors,soldiers,musketeers,mercenaries,created_at,updated_at)
                values('Surface Contract Build',(select slug from build_roles order by sort_order,slug limit 1),
                    :shipId,(select id from users where is_bootstrap_admin=true),false,false,:sailors,0,0,0,current_timestamp,current_timestamp)
                returning id
                """, Map.of("shipId", ship.get("id"), "sailors", ship.get("sailor_minimum")));
    }

    private String queryValue(ContractOperation operation, String name, Map<String, Object> schema) {
        Map<String, Object> concrete = concreteSchema(schema);
        return switch (name) {
            case "from_date" -> "2030-01-01";
            case "to_date" -> "2030-02-01";
            case "start" -> "2030-01-01T00:00:00Z";
            case "end" -> "2030-02-01T00:00:00Z";
            case "category" -> categoryValue(operation.template());
            case "client_ip" -> "127.0.0.1";
            case "fleet_id" -> pathValue("fleet_id");
            case "ship_id" -> String.valueOf(jdbc.required("select id from ships order by id limit 1", Map.of()).get("id"));
            case "squad_id", "webhook_id" -> String.valueOf(SENTINEL_ID);
            case "min_ship_rate" -> "1";
            case "max_ship_rate" -> "7";
            default -> schemaValue(concrete);
        };
    }

    private static String categoryValue(String path) {
        if (path.contains("/forum/") || path.contains("/guides")) return "general";
        return "other";
    }

    private String schemaValue(Map<String, Object> schema) {
        Object defaultValue = schema.get("default");
        if (defaultValue != null) return String.valueOf(defaultValue);
        Object enumValue = schema.get("enum");
        if (enumValue instanceof List<?> values && !values.isEmpty()) return String.valueOf(values.getFirst());
        String pattern = string(schema.get("pattern"));
        Matcher alternatives = SIMPLE_ALTERNATION.matcher(pattern);
        if (alternatives.matches()) return alternatives.group(1).split("\\|")[0];
        String format = string(schema.get("format"));
        if ("date".equals(format)) return "2030-01-15";
        if ("date-time".equals(format)) return "2030-01-15T12:00:00Z";
        String type = string(schema.get("type"));
        if ("boolean".equals(type)) return "true";
        if ("integer".equals(type) || "number".equals(type)) {
            Object minimum = schema.get("minimum");
            return minimum == null ? "1" : String.valueOf(((Number) minimum).longValue());
        }
        return "integration";
    }

    private Map<String, Object> concreteSchema(Map<String, Object> schema) {
        Object anyOf = schema.get("anyOf");
        if (!(anyOf instanceof List<?> alternatives)) return schema;
        for (Object raw : alternatives) {
            if (!(raw instanceof Map<?, ?>)) continue;
            Map<String, Object> candidate = map(raw);
            if (!"null".equals(candidate.get("type"))) return candidate;
        }
        return schema;
    }

    private HttpResponse<String> send(String method, String path, String body, SessionCookies session,
                                      boolean sameOrigin) throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(origin() + path));
        if (sameOrigin && !"GET".equals(method)) request.header("Origin", origin());
        if (session != null) {
            request.header("Cookie", session.cookieHeader());
            if (!"GET".equals(method)) request.header("X-XSRF-TOKEN", session.csrfToken());
        }
        if (body != null) {
            request.header("Content-Type", "application/json");
            request.method(method, HttpRequest.BodyPublishers.ofString(body));
        } else {
            request.method(method, HttpRequest.BodyPublishers.noBody());
        }
        return http.send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> sendWithoutCsrf(String method, String path, String body, SessionCookies session)
            throws Exception {
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(origin() + path))
                .header("Origin", origin())
                .header("Cookie", session.cookieHeader());
        if (body != null) {
            request.header("Content-Type", "application/json");
            request.method(method, HttpRequest.BodyPublishers.ofString(body));
        } else {
            request.method(method, HttpRequest.BodyPublishers.noBody());
        }
        return http.send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> sendEmptyMultipartWithoutCsrf(String method, String path, SessionCookies session)
            throws Exception {
        String boundary = "rbf-api-surface-csrf-boundary";
        HttpRequest request = HttpRequest.newBuilder(URI.create(origin() + path))
                .header("Origin", origin())
                .header("Cookie", session.cookieHeader())
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .method(method, HttpRequest.BodyPublishers.ofString("--" + boundary + "--\r\n"))
                .build();
        return http.send(request, HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> sendEmptyMultipart(String method, String path, SessionCookies session) throws Exception {
        String boundary = "rbf-api-surface-boundary";
        HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(origin() + path))
                .header("Origin", origin())
                .header("Content-Type", "multipart/form-data; boundary=" + boundary);
        if (session != null) {
            request.header("Cookie", session.cookieHeader());
            request.header("X-XSRF-TOKEN", session.csrfToken());
        }
        request.method(method, HttpRequest.BodyPublishers.ofString("--" + boundary + "--\r\n"));
        return http.send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private SessionCookies anonymousCsrf() throws Exception {
        HttpResponse<String> response = send("GET", "/api/auth/me", null, null, true);
        assertThat(response.statusCode()).as("anonymous CSRF bootstrap response=%s", excerpt(response.body())).isEqualTo(200);
        String csrf = cookieValue(response, "XSRF-TOKEN");
        return new SessionCookies("XSRF-TOKEN=" + csrf, csrf);
    }

    private SessionCookies login() throws Exception {
        HttpResponse<String> login = send("POST", "/api/auth/login",
                "{\"username\":\"admin\",\"password\":\"" + ADMIN_PASSWORD + "\"}", null, true);
        assertThat(login.statusCode()).as("bootstrap admin login response=%s", excerpt(login.body())).isEqualTo(200);
        String session = "rbf_hub_session=" + cookieValue(login, "rbf_hub_session");
        HttpResponse<String> me = send("GET", "/api/auth/me", null, new SessionCookies(session, ""), true);
        return new SessionCookies(session, cookieValue(me, "XSRF-TOKEN"));
    }

    private static boolean isCsrfBootstrapOperation(ContractOperation operation) {
        return "POST".equals(operation.method()) && List.of(
                "/api/auth/login", "/api/auth/register",
                "/api/privacy/cookie-consent", "/api/privacy/contact").contains(operation.template());
    }

    private static boolean isPublicOperation(ContractOperation operation) {
        String path = operation.template();
        if ("GET".equals(operation.method())) {
            return List.of(
                    "/api/health", "/api/health/ready", "/api/auth/me", "/api/legal-notice",
                    "/api/privacy/cookie-consent", "/api/privacy/cookie-policy", "/api/fleets/public/official",
                    "/api/files/{file_id}/content").contains(path);
        }
        return "POST".equals(operation.method()) && List.of(
                "/api/auth/login", "/api/auth/logout", "/api/auth/register",
                "/api/privacy/cookie-consent", "/api/privacy/contact").contains(path);
    }

    private static void assertNoServerError(HttpResponse<String> response, String method, String path) {
        assertThat(response.statusCode())
                .as("%s %s returned %s; response=%s", method, path, response.statusCode(), excerpt(response.body()))
                .isLessThan(500);
    }

    private static String cookieValue(HttpResponse<String> response, String name) {
        Pattern pattern = Pattern.compile(COOKIE_VALUE.pattern().formatted(Pattern.quote(name)));
        return response.headers().allValues("set-cookie").stream()
                .map(pattern::matcher)
                .filter(Matcher::find)
                .map(matcher -> matcher.group(1))
                .findFirst()
                .orElseThrow(() -> new AssertionError("Missing cookie " + name));
    }

    private static String excerpt(String body) {
        if (body == null) return "";
        String normalized = body.replaceAll("[\\r\\n\\t]+", " ");
        return normalized.substring(0, Math.min(500, normalized.length()));
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object value) {
        return value instanceof Map<?, ?> ? (Map<String, Object>) value : Map.of();
    }

    private static String string(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    private String origin() {
        return "http://localhost:" + port;
    }

    private record ContractOperation(String method, String template, Map<String, Object> pathItem,
                                     Map<String, Object> operation) { }

    private record SessionCookies(String sessionCookie, String csrfToken) {
        String cookieHeader() {
            return csrfToken == null || csrfToken.isBlank()
                    ? sessionCookie
                    : sessionCookie + "; XSRF-TOKEN=" + csrfToken;
        }
    }
}
