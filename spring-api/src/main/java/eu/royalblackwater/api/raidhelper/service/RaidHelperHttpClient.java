package eu.royalblackwater.api.raidhelper.service;

import eu.royalblackwater.api.raidhelper.dto.RaidHelperConnectionDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperJsonPayloadDto;
import eu.royalblackwater.api.security.service.SecretBoxException;
import eu.royalblackwater.api.security.service.FernetSecretBox;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Component
public class RaidHelperHttpClient {
    private static final int MAX_RESPONSE_BYTES = 1_048_576;
    private final HttpClient client;
    private final ObjectMapper json;
    private final FernetSecretBox secrets;
    private final RaidHelperPolicy policy;

    @Autowired
    public RaidHelperHttpClient(ObjectMapper json, FernetSecretBox secrets, RaidHelperPolicy policy) {
        this(HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5))
                .followRedirects(HttpClient.Redirect.NEVER).build(), json, secrets, policy);
    }

    RaidHelperHttpClient(HttpClient client, ObjectMapper json, FernetSecretBox secrets, RaidHelperPolicy policy) {
        this.client = client;
        this.json = json;
        this.secrets = secrets;
        this.policy = policy;
    }

    public Response request(RaidHelperConnectionDto connection, String method, String path, RaidHelperJsonPayloadDto payload) {
        if (!path.startsWith("/") || path.contains("..")) {
            throw new RaidHelperTransportException("Invalid Raid-Helper request path.");
        }
        String apiKey;
        try {
            apiKey = normalizeKey(secrets.decrypt(connection.apiKeyEncrypted()));
        } catch (SecretBoxException exception) {
            throw new RaidHelperTransportException("Stored Raid-Helper API key could not be decrypted.", exception);
        }
        HttpRequest.BodyPublisher body = payload == null
                ? HttpRequest.BodyPublishers.noBody()
                : HttpRequest.BodyPublishers.ofString(writeJson(payload.values()), StandardCharsets.UTF_8);
        HttpRequest request = HttpRequest.newBuilder(URI.create(policy.baseUrl(connection.apiBaseUrl()) + path))
                .timeout(Duration.ofSeconds(10))
                .header("Authorization", apiKey)
                .header("Accept", "application/json")
                .header("Content-Type", "application/json; charset=utf-8")
                .header("User-Agent", "RoyalBlackwaterFleet-RaidHelper/2.0")
                .method(method.toUpperCase(java.util.Locale.ROOT), body)
                .build();
        try {
            HttpResponse<InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
            try (InputStream stream = response.body()) {
                byte[] bytes = stream.readNBytes(MAX_RESPONSE_BYTES + 1);
                if (bytes.length > MAX_RESPONSE_BYTES) {
                    throw new RaidHelperTransportException("Raid-Helper response exceeded the safety limit.");
                }
                return new Response(response.statusCode(), parseBody(new String(bytes, StandardCharsets.UTF_8)));
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new RaidHelperTransportException("Raid-Helper request was interrupted.", exception);
        } catch (IOException | IllegalArgumentException exception) {
            throw new RaidHelperTransportException("Raid-Helper connection failed.", exception);
        }
    }

    public String externalId(Object body) {
        if (body instanceof Map<?, ?> values) {
            for (String key : new String[]{"id", "eventId", "event_id", "messageId", "message_id"}) {
                if (values.get(key) != null) return String.valueOf(values.get(key));
            }
            return externalId(values.get("event"));
        }
        return null;
    }

    public String failureMessage(Response response) {
        String reason = responseReason(response.body());
        String base = response.statusCode() == 401
                ? "Raid-Helper rejected this event payload (HTTP 401). Verify the API key, destination and optional template permissions."
                : "Raid-Helper returned HTTP " + response.statusCode() + ".";
        return reason == null ? base : base + " " + reason;
    }

    private Object parseBody(String text) {
        if (text == null || text.isBlank()) return null;
        try {
            return json.readValue(text, Object.class);
        } catch (JacksonException exception) {
            return text.length() > 1000 ? text.substring(0, 1000) : text;
        }
    }

    private String writeJson(Map<String, Object> payload) {
        try {
            return json.writeValueAsString(payload);
        } catch (JacksonException exception) {
            throw new RaidHelperTransportException("Raid-Helper payload could not be serialized.", exception);
        }
    }

    private static String normalizeKey(String raw) {
        String value = raw.strip();
        if (value.regionMatches(true, 0, "Bearer ", 0, 7)) value = value.substring(7).strip();
        if (value.length() >= 2 && value.charAt(0) == value.charAt(value.length() - 1)
                && (value.charAt(0) == '\'' || value.charAt(0) == '"')) {
            value = value.substring(1, value.length() - 1).strip();
        }
        if (value.isEmpty() || value.indexOf('\r') >= 0 || value.indexOf('\n') >= 0) {
            throw new RaidHelperTransportException("Stored Raid-Helper API key is malformed.");
        }
        return value;
    }

    private static String responseReason(Object body) {
        if (!(body instanceof Map<?, ?> values)) return null;
        for (String key : new String[]{"message", "error", "detail"}) {
            Object value = values.get(key);
            if (value instanceof String text && !text.isBlank()) {
                String clean = text.replaceAll("\\s+", " ").strip();
                return clean.length() > 240 ? clean.substring(0, 240) : clean;
            }
        }
        return null;
    }

    public record Response(int statusCode, Object body) {
        public boolean successful() {
            return statusCode >= 200 && statusCode < 300;
        }
    }

    public static class RaidHelperTransportException extends RuntimeException {
        private static final long serialVersionUID = 1L;

        public RaidHelperTransportException(String message) { super(message); }
        public RaidHelperTransportException(String message, Throwable cause) { super(message, cause); }
    }
}
