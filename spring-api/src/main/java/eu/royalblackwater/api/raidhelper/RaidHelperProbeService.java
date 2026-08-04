package eu.royalblackwater.api.raidhelper;

import static eu.royalblackwater.api.persistence.RowValues.*;

import eu.royalblackwater.api.contract.RaidHelperDestinationTestRequest;
import eu.royalblackwater.api.contract.RaidHelperProfileTestResult;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class RaidHelperProbeService {
    private final JdbcQueryService jdbc;
    private final RaidHelperProfileService profiles;
    private final RaidHelperDestinationService destinations;
    private final RaidHelperTemplateService templates;
    private final RaidHelperHttpClient client;
    private final RaidHelperPayloadRenderer renderer;
    private final Clock clock;

    public RaidHelperProbeService(JdbcQueryService jdbc, RaidHelperProfileService profiles,
                                  RaidHelperDestinationService destinations, RaidHelperTemplateService templates,
                                  RaidHelperHttpClient client, RaidHelperPayloadRenderer renderer, Clock clock) {
        this.jdbc = jdbc;
        this.profiles = profiles;
        this.destinations = destinations;
        this.templates = templates;
        this.client = client;
        this.renderer = renderer;
        this.clock = clock;
    }

    public RaidHelperProfileTestResult profile(AuthenticatedUser actor, long profileId) {
        RaidHelperProfileService.requireAdmin(actor);
        Map<String, Object> row = profiles.encryptedProfile(profileId);
        try {
            RaidHelperHttpClient.Response response = client.request(row, "GET",
                    "/servers/" + requiredString(row, "server_id") + "/events", null);
            String message = response.successful()
                    ? "Raid-Helper server read access succeeded. Test the exact channel destination to verify event creation."
                    : "Raid-Helper rejected the saved profile or server configuration.";
            return result(response.successful(), response.statusCode(), message);
        } catch (RuntimeException exception) {
            return result(false, null, "Raid-Helper connection failed.");
        }
    }

    public RaidHelperProfileTestResult destination(
            AuthenticatedUser actor, long destinationId, RaidHelperDestinationTestRequest request) {
        RaidHelperProfileService.requireAdmin(actor);
        Map<String, Object> destination = destinationWithProfile(destinationId);
        String leaderId = string(destination, "default_leader_id");
        if (leaderId == null) {
            return result(false, null, "Configure a default leader ID before testing this destination.");
        }
        boolean minimal = request != null && Boolean.TRUE.equals(request.useMinimalPayload());
        Map<String, Object> template = minimal ? null : testTemplate(destination, request == null ? null : request.templateId());
        Map<String, Object> payload = minimal ? minimalPayload(leaderId) : renderer.render(testEvent(destination, template), template, leaderId);
        String path = "/servers/" + requiredString(destination, "server_id")
                + "/channels/" + requiredString(destination, "channel_id") + "/event";
        try {
            RaidHelperHttpClient.Response create = client.request(destination, "POST", path, payload);
            if (!create.successful()) {
                return result(false, create.statusCode(), client.failureMessage(create));
            }
            String externalId = client.externalId(create.body());
            if (externalId == null) {
                return result(false, create.statusCode(),
                        "The temporary event was created, but Raid-Helper returned no event ID for cleanup.");
            }
            RaidHelperHttpClient.Response delete = client.request(destination, "DELETE", "/events/" + externalId, null);
            if (!delete.successful()) {
                return result(false, delete.statusCode(),
                        "The temporary event was created, but automatic cleanup failed. " + client.failureMessage(delete));
            }
            String label = minimal ? "minimal default payload" : "selected application template";
            return result(true, create.statusCode(),
                    "Raid-Helper event creation and cleanup succeeded for " + label + ".");
        } catch (RuntimeException exception) {
            return result(false, null, "Raid-Helper destination test failed.");
        }
    }

    private Map<String, Object> destinationWithProfile(long id) {
        destinations.detail(id);
        return jdbc.required("""
                select d.*,p.name profile_name,p.server_id,p.api_key_encrypted,p.api_base_url,p.timezone,
                       p.default_leader_id,p.is_active profile_active,s.name squad_name
                from raid_helper_destinations d join raid_helper_profiles p on p.id=d.profile_id
                left join squads s on s.id=d.squad_id where d.id=:id
                """, Map.of("id", id));
    }

    private Map<String, Object> testTemplate(Map<String, Object> destination, Long requestedId) {
        Map<String, Object> template;
        if (requestedId == null) {
            template = jdbc.optional("""
                    select t.*,p.timezone,p.name profile_name from raid_helper_templates t
                    join raid_helper_profiles p on p.id=t.profile_id
                    where t.profile_id=:profileId and t.is_active=true
                    order by t.is_default desc,t.id limit 1
                    """, Map.of("profileId", longValue(destination, "profile_id"))).orElse(null);
            if (template == null) {
                throw new IllegalArgumentException("No active Raid-Helper template is configured for this profile.");
            }
        } else {
            template = new LinkedHashMap<>(templates.detail(requestedId));
            template.put("timezone", requiredString(destination, "timezone"));
            if (longValue(template, "profile_id") != longValue(destination, "profile_id")
                    || !booleanValue(template, "is_active")) {
                throw new IllegalArgumentException(
                        "The selected Raid-Helper template is inactive or belongs to another profile.");
            }
        }
        return template;
    }

    private Map<String, Object> testEvent(Map<String, Object> destination, Map<String, Object> template) {
        LocalDateTime start = LocalDateTime.ofInstant(clock.instant().plusSeconds(900), ZoneOffset.UTC);
        String category = jdbc.optional("""
                select category from raid_helper_template_categories where template_id=:id order by category limit 1
                """, Map.of("id", longValue(template, "id")))
                .map(row -> requiredString(row, "category"))
                .orElseGet(() -> jdbc.optional("""
                        select category from raid_helper_destination_categories
                        where destination_id=:id order by category limit 1
                        """, Map.of("id", longValue(destination, "id")))
                        .map(row -> requiredString(row, "category")).orElse("meeting"));
        Map<String, Object> event = new LinkedHashMap<>();
        event.put("event_id", 0L);
        event.put("title", "Royal Blackwater Fleet connection test");
        event.put("category", category);
        event.put("description", "Temporary API verification event. It should be removed automatically.");
        event.put("location", "Raid-Helper API test");
        event.put("start_at", start);
        event.put("end_at", start.plusHours(1));
        event.put("all_day", false);
        event.put("squad_id", nullableLong(destination, "squad_id"));
        event.put("squad_name", string(destination, "squad_name"));
        return event;
    }

    private Map<String, Object> minimalPayload(String leaderId) {
        java.time.ZonedDateTime start = clock.instant().plusSeconds(900).atZone(ZoneOffset.UTC);
        return Map.of("leaderId", leaderId, "title", "Royal Blackwater Fleet connection test",
                "description", "Temporary API verification event. It should be removed automatically.",
                "date", java.time.format.DateTimeFormatter.ofPattern("dd.MM.uuuu").format(start),
                "time", java.time.format.DateTimeFormatter.ofPattern("HH:mm").format(start));
    }

    private static RaidHelperProfileTestResult result(boolean ok, Integer status, String message) {
        return new RaidHelperProfileTestResult(message, ok, status == null ? null : status.longValue());
    }
}
