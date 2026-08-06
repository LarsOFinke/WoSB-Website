package eu.royalblackwater.api.raidhelper.service;

import java.net.URI;
import java.net.URISyntaxException;
import java.time.DateTimeException;
import java.time.ZoneId;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Component
public class RaidHelperPolicy {
    public static final Set<String> EVENT_CATEGORIES = Set.of(
            "port_battle", "training", "fleet_farm", "operation", "meeting", "other");
    public static final String DEFAULT_API_URL = "https://raid-helper.xyz/api/v4";
    public static final String DEFAULT_TIMEZONE = "Europe/Berlin";
    public static final String FREE_PAYLOAD_TEMPLATE = """
            {
              "title": "{{rendered.title}}",
              "description": "{{rendered.description}}",
              "date": "{{event.date}}",
              "time": "{{event.time}}",
              "duration": "{{event.duration_minutes}}"
            }
            """;
    private static final Set<String> ALLOWED_API_HOSTS = Set.of(
            "raid-helper.dev", "www.raid-helper.dev", "raid-helper.xyz", "www.raid-helper.xyz");
    private static final Set<String> FREE_PAYLOAD_KEYS = Set.of(
            "title", "description", "date", "time", "duration", "leaderId");

    private final ObjectMapper json;

    public RaidHelperPolicy(ObjectMapper json) {
        this.json = json;
    }

    public String baseUrl(String raw) {
        String value = blankToDefault(raw, DEFAULT_API_URL).strip();
        try {
            URI uri = new URI(value);
            String host = uri.getHost() == null ? "" : uri.getHost().toLowerCase(Locale.ROOT);
            String path = uri.getPath() == null ? "" : uri.getPath().replaceAll("/+$", "");
            if (!"https".equalsIgnoreCase(uri.getScheme()) || !ALLOWED_API_HOSTS.contains(host)) {
                throw bad("Raid-Helper API URL must use an official HTTPS host.");
            }
            if (!path.endsWith("/api/v4")) {
                throw bad("Raid-Helper API URL must end with /api/v4.");
            }
            if (uri.getQuery() != null || uri.getFragment() != null || uri.getUserInfo() != null) {
                throw bad("Raid-Helper API URL contains unsupported components.");
            }
            return "https://raid-helper.xyz" + path;
        } catch (URISyntaxException exception) {
            throw bad("Raid-Helper API URL is invalid.");
        }
    }

    public String timezone(String raw) {
        String value = blankToDefault(raw, DEFAULT_TIMEZONE).strip();
        try {
            ZoneId.of(value);
            return value;
        } catch (DateTimeException exception) {
            throw bad("Raid-Helper timezone must be a valid IANA timezone.");
        }
    }

    public List<String> categories(List<String> raw) {
        LinkedHashSet<String> result = new LinkedHashSet<>();
        for (String value : raw == null ? List.<String>of() : raw) {
            if (value == null || value.isBlank()) continue;
            String category = value.strip().toLowerCase(Locale.ROOT);
            if (!EVENT_CATEGORIES.contains(category)) {
                throw bad("Invalid event category: " + category);
            }
            result.add(category);
        }
        return result.stream().sorted().toList();
    }

    public String category(String raw) {
        String value = raw == null ? "" : raw.strip().toLowerCase(Locale.ROOT);
        if (!EVENT_CATEGORIES.contains(value)) {
            throw bad("Invalid event category.");
        }
        return value;
    }

    public String payloadTemplate(String raw, String raidTemplateId, boolean premium) {
        String value = blankToDefault(raw, FREE_PAYLOAD_TEMPLATE);
        Object decoded;
        try {
            decoded = json.readValue(value, Object.class);
        } catch (JacksonException exception) {
            throw bad("Raid-Helper payload template must contain valid JSON.");
        }
        if (!(decoded instanceof Map<?, ?> payload)) {
            throw bad("Raid-Helper payload template must be a JSON object.");
        }
        if (!premium) {
            Set<String> keys = payload.keySet().stream().map(String::valueOf).collect(java.util.stream.Collectors.toSet());
            Set<String> missing = new java.util.TreeSet<>(Set.of("title", "date", "time"));
            missing.removeAll(keys);
            if (!missing.isEmpty()) {
                throw bad("A free-compatible Raid-Helper payload must include: " + String.join(", ", missing) + ".");
            }
            Set<String> advanced = new java.util.TreeSet<>(keys);
            advanced.removeAll(FREE_PAYLOAD_KEYS);
            String normalizedTemplate = normalizedTemplateId(raidTemplateId);
            if (normalizedTemplate == null) advanced.remove("templateId");
            if (normalizedTemplate != null || !advanced.isEmpty()) {
                throw bad("This Raid-Helper template uses Premium/custom payload features without explicit enablement.");
            }
        }
        try {
            return json.writerWithDefaultPrettyPrinter().writeValueAsString(decoded);
        } catch (JacksonException exception) {
            throw new IllegalStateException("Validated Raid-Helper payload could not be serialized.", exception);
        }
    }

    public String normalizedTemplateId(String raw) {
        if (raw == null || raw.isBlank() || "standard".equalsIgnoreCase(raw.strip())) return null;
        return raw.strip();
    }

    public String numericIdentifier(String raw, String label, boolean required) {
        String value = raw == null ? "" : raw.strip();
        if (value.isEmpty() && !required) return null;
        if (!value.matches("[0-9]{5,32}")) throw bad(label + " must contain 5 to 32 digits.");
        return value;
    }

    public String cleanName(String raw, String label) {
        String value = raw == null ? "" : raw.strip();
        if (value.isEmpty()) throw bad(label + " is required.");
        return value;
    }

    public boolean flag(Boolean value, boolean fallback) {
        return value == null ? fallback : value;
    }

    private static String blankToDefault(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value;
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }
}
