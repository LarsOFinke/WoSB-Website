package eu.royalblackwater.api.raidhelper;

import static eu.royalblackwater.api.persistence.RowValues.*;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;

@Component
public class RaidHelperDeliveryWorker {
    private static final int BATCH_SIZE = 10;
    private static final int ERROR_LIMIT = 1000;
    private final JdbcQueryService jdbc;
    private final RaidHelperHttpClient client;
    private final RaidHelperPayloadRenderer payloads;
    private final TransactionTemplate transactions;
    private final Clock clock;

    public RaidHelperDeliveryWorker(JdbcQueryService jdbc, RaidHelperHttpClient client,
                                    RaidHelperPayloadRenderer payloads,
                                    TransactionTemplate transactions, Clock clock) {
        this.jdbc = jdbc;
        this.client = client;
        this.payloads = payloads;
        this.transactions = transactions;
        this.clock = clock;
    }

    @Scheduled(fixedDelayString = "${rbf.raid-helper.delivery-delay:PT15S}")
    public void deliverQueuedLinks() {
        recoverAbandonedClaims();
        for (int index = 0; index < BATCH_SIZE; index++) {
            Long linkId = claim();
            if (linkId == null) return;
            deliver(linkId);
        }
    }

    private Long claim() {
        return transactions.execute(status -> {
            var row = jdbc.optional("""
                    with candidate as (
                      select id from raid_helper_event_links where status='queued'
                      order by updated_at,id for update skip locked limit 1
                    )
                    update raid_helper_event_links l set status='processing',attempts=attempts+1,
                      last_attempt_at=:now,updated_at=:now from candidate c where l.id=c.id
                    returning l.id
                    """, Map.of("now", now()));
            return row.map(value -> longValue(value, "id")).orElse(null);
        });
    }

    private void deliver(long linkId) {
        Map<String, Object> link = detail(linkId);
        String operation = requiredString(link, "last_operation");
        try {
            if (!"delete".equals(operation)
                    && (!booleanValue(link, "destination_active")
                    || !booleanValue(link, "profile_active")
                    || !booleanValue(link, "template_active"))) {
                throw new RaidHelperHttpClient.RaidHelperTransportException(
                        "Raid-Helper profile, destination or template is inactive.");
            }
            String externalId = string(link, "external_event_id");
            if ("delete".equals(operation) && externalId == null) {
                deleteLink(linkId);
                return;
            }
            RaidHelperHttpClient.Response response;
            if ("delete".equals(operation)) {
                response = client.request(link, "DELETE", "/events/" + externalId, null);
            } else {
                String leaderId = string(link, "leader_id_override");
                if (leaderId == null) leaderId = string(link, "default_leader_id");
                if (leaderId == null) {
                    throw new RaidHelperHttpClient.RaidHelperTransportException(
                            "Raid-Helper leader ID is missing for this event.");
                }
                Map<String, Object> payload = payloads.render(link, link, leaderId);
                if (externalId == null) {
                    String path = "/servers/" + requiredString(link, "server_id")
                            + "/channels/" + requiredString(link, "channel_id") + "/event";
                    response = client.request(link, "POST", path, payload);
                } else {
                    response = client.request(link, "PATCH", "/events/" + externalId, payload);
                }
            }
            if (!response.successful()) {
                fail(linkId, response.statusCode(), client.failureMessage(response));
                return;
            }
            if ("delete".equals(operation)) {
                deleteLink(linkId);
                return;
            }
            String deliveredId = externalId;
            if (deliveredId == null) {
                deliveredId = client.externalId(response.body());
                if (deliveredId == null || deliveredId.isBlank()) {
                    fail(linkId, response.statusCode(), "Raid-Helper response did not include an event ID.");
                    return;
                }
            }
            succeed(linkId, deliveredId, response.statusCode(), externalId == null ? "create" : "update");
        } catch (RuntimeException exception) {
            fail(linkId, null, safeMessage(exception));
        }
    }

    private Map<String, Object> detail(long linkId) {
        return jdbc.required("""
                select l.*,e.title,e.category,e.description,e.location,e.start_at,e.end_at,e.all_day,e.squad_id,
                       s.name squad_name,d.channel_id,d.is_active destination_active,
                       p.server_id,p.api_key_encrypted,p.api_base_url,p.timezone,p.default_leader_id,
                       p.is_active profile_active,t.raid_template_id,t.title_template,t.description_template,
                       t.announcement_template,t.payload_template_json,t.is_active template_active
                from raid_helper_event_links l join fleet_events e on e.id=l.event_id
                left join squads s on s.id=e.squad_id
                join raid_helper_destinations d on d.id=l.destination_id
                join raid_helper_profiles p on p.id=d.profile_id
                join raid_helper_templates t on t.id=l.template_id
                where l.id=:id
                """, Map.of("id", linkId));
    }

    private void recoverAbandonedClaims() {
        transactions.executeWithoutResult(status -> jdbc.update("""
                update raid_helper_event_links set status='queued',
                  error_message='Previous delivery attempt was interrupted and has been re-queued.',updated_at=:now
                where status='processing' and last_attempt_at < :cutoff
                """, Map.of("now", now(), "cutoff", now().minusMinutes(15))));
    }

    private void succeed(long id, String externalId, int responseStatus, String operation) {
        transactions.executeWithoutResult(status -> jdbc.update("""
                update raid_helper_event_links set status='delivered',external_event_id=:externalId,
                  response_status=:responseStatus,last_operation=:operation,error_message=null,
                  synced_at=:now,updated_at=:now where id=:id
                """, Map.of("externalId", externalId, "responseStatus", responseStatus,
                "operation", operation, "now", now(), "id", id)));
    }

    private void fail(long id, Integer responseStatus, String message) {
        transactions.executeWithoutResult(status -> jdbc.update("""
                update raid_helper_event_links set status='failed',response_status=:responseStatus,
                  error_message=:message,updated_at=:now where id=:id
                """, SqlParameters.ofNullable("responseStatus", responseStatus,
                "message", truncate(message), "now", now(), "id", id)));
    }

    private void deleteLink(long id) {
        transactions.executeWithoutResult(status -> jdbc.update(
                "delete from raid_helper_event_links where id=:id", Map.of("id", id)));
    }

    private String safeMessage(RuntimeException exception) {
        String value = exception.getMessage();
        if (value == null || value.isBlank()) return "Raid-Helper delivery failed.";
        return truncate(value);
    }

    private static String truncate(String value) {
        String clean = value.replaceAll("\\s+", " ").strip();
        return clean.length() > ERROR_LIMIT ? clean.substring(0, ERROR_LIMIT) : clean;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }
}
