package eu.royalblackwater.api.raidhelper.mapper;

import eu.royalblackwater.api.raidhelper.dto.RaidHelperEventDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperJsonPayloadDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperTemplateConfigDto;
import java.time.Duration;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

@Component
public class RaidHelperPayloadRenderer {
    private static final Pattern TOKEN = Pattern.compile("\\{\\{\\s*([a-zA-Z0-9_.-]+)\\s*}}", Pattern.MULTILINE);
    private static final Pattern EXACT_TOKEN = Pattern.compile("^\\s*\\{\\{\\s*([a-zA-Z0-9_.-]+)\\s*}}\\s*$");
    private static final DateTimeFormatter DATE = DateTimeFormatter.ofPattern("dd.MM.uuuu");
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm");

    private final ObjectMapper json;
    public RaidHelperPayloadRenderer(ObjectMapper json) {
        this.json = json;
    }

    public RaidHelperJsonPayloadDto render(
            RaidHelperEventDto event, RaidHelperTemplateConfigDto template, String leaderId) {
        Map<String, Object> context = context(event, template);
        Map<String, Object> rendered = Map.of(
                "title", renderText(template.titleTemplate(), context),
                "description", renderText(template.descriptionTemplate(), context),
                "announcement", renderText(template.announcementTemplate(), context));
        context.put("rendered", rendered);
        Object raw;
        try {
            raw = json.readValue(template.payloadTemplateJson(), Object.class);
        } catch (JacksonException exception) {
            throw bad("Raid-Helper payload template contains invalid JSON.");
        }
        Object result = renderValue(raw, context);
        if (!(result instanceof Map<?, ?> rawMap)) {
            throw bad("Raid-Helper payload template must render to a JSON object.");
        }
        Map<String, Object> payload = new LinkedHashMap<>();
        rawMap.forEach((key, value) -> payload.put(String.valueOf(key), value));
        if (normalizedTemplateId(template.raidTemplateId()) == null
                || String.valueOf(payload.getOrDefault("templateId", "")).isBlank()) {
            payload.remove("templateId");
        }
        payload.put("leaderId", leaderId);
        return RaidHelperJsonPayloadDto.of(payload);
    }

    private Map<String, Object> context(RaidHelperEventDto event, RaidHelperTemplateConfigDto template) {
        ZonedDateTime startUtc = event.startAt().atZone(ZoneOffset.UTC);
        ZonedDateTime endUtc = event.endAt().atZone(ZoneOffset.UTC);
        ZoneId zone = ZoneId.of(template.timezone());
        ZonedDateTime start = startUtc.withZoneSameInstant(zone);
        ZonedDateTime end = endUtc.withZoneSameInstant(zone);
        long duration = Math.max(1, Duration.between(startUtc, endUtc).toMinutes());
        String offset = start.getOffset().getId();
        if ("Z".equals(offset)) offset = "+00:00";

        Map<String, Object> eventValues = new LinkedHashMap<>();
        eventValues.put("id", event.eventId());
        eventValues.put("title", event.title());
        eventValues.put("category", event.category());
        eventValues.put("description", nullToEmpty(event.description()));
        eventValues.put("location", nullToEmpty(event.location()));
        eventValues.put("start_at", start.toOffsetDateTime().toString());
        eventValues.put("end_at", end.toOffsetDateTime().toString());
        eventValues.put("start_at_utc", startUtc.toOffsetDateTime().toString());
        eventValues.put("end_at_utc", endUtc.toOffsetDateTime().toString());
        eventValues.put("start_unix", startUtc.toEpochSecond());
        eventValues.put("end_unix", endUtc.toEpochSecond());
        eventValues.put("date", DATE.format(start));
        eventValues.put("time", TIME.format(start));
        eventValues.put("duration_minutes", duration);
        eventValues.put("all_day", event.allDay());
        eventValues.put("timezone", template.timezone());
        eventValues.put("timezone_abbreviation", start.getZone().getId());
        eventValues.put("utc_offset", offset);
        eventValues.put("start_discord", "<t:" + startUtc.toEpochSecond() + ":F>");
        eventValues.put("end_discord", "<t:" + endUtc.toEpochSecond() + ":F>");
        eventValues.put("start_discord_relative", "<t:" + startUtc.toEpochSecond() + ":R>");

        Map<String, Object> context = new LinkedHashMap<>();
        context.put("event", eventValues);
        context.put("scope", Map.of(
                "type", event.squadId() == null ? "fleet" : "squad",
                "name", event.squadName() == null ? "Fleet" : event.squadName(),
                "squad_id", event.squadId() == null ? "" : event.squadId()));
        context.put("raid_helper", new LinkedHashMap<>(Map.of(
                "template_id", nullToEmpty(normalizedTemplateId(template.raidTemplateId())))));
        return context;
    }

    private Object renderValue(Object value, Map<String, Object> context) {
        if (value instanceof String text) {
            Matcher exact = EXACT_TOKEN.matcher(text);
            return exact.matches() ? value(context, exact.group(1)) : renderText(text, context);
        }
        if (value instanceof List<?> values) {
            return values.stream().map(item -> renderValue(item, context)).toList();
        }
        if (value instanceof Map<?, ?> values) {
            Map<String, Object> rendered = new LinkedHashMap<>();
            values.forEach((key, item) -> {
                if (item != null) rendered.put(String.valueOf(key), renderValue(item, context));
            });
            return rendered;
        }
        return value;
    }

    private String renderText(String template, Map<String, Object> context) {
        Matcher matcher = TOKEN.matcher(template);
        StringBuilder result = new StringBuilder();
        while (matcher.find()) {
            matcher.appendReplacement(result, Matcher.quoteReplacement(String.valueOf(value(context, matcher.group(1)))));
        }
        matcher.appendTail(result);
        return result.toString();
    }

    private static Object value(Map<String, Object> context, String path) {
        Object current = context;
        for (String segment : path.split("\\.")) {
            if (!(current instanceof Map<?, ?> values) || !values.containsKey(segment)) return "";
            current = values.get(segment);
        }
        return current == null ? "" : current;
    }

    private static String nullToEmpty(String value) {
        return value == null ? "" : value;
    }

    private static String normalizedTemplateId(String raw) {
        if (raw == null || raw.isBlank() || "standard".equalsIgnoreCase(raw.strip())) return null;
        return raw.strip();
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(BAD_REQUEST, message);
    }
}
