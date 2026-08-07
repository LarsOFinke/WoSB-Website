package eu.royalblackwater.api.raidhelper.service;

import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperDeliveryDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperJsonPayloadDto;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperDtoMapper;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperPayloadRenderer;
import eu.royalblackwater.api.raidhelper.repository.RaidHelperRepository;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperDeliveryQueries;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;

import static eu.royalblackwater.api.persistence.RowValues.longValue;

@Component
public class RaidHelperDeliveryWorker {
    private static final int BATCH_SIZE = 10;
    private static final int ERROR_LIMIT = 1000;
    private final RaidHelperRepository repository;
    private final RaidHelperHttpClient client;
    private final RaidHelperPayloadRenderer payloads;
    private final TransactionTemplate transactions;
    private final Clock clock;
    private final RaidHelperDtoMapper mapper;

    public RaidHelperDeliveryWorker(RaidHelperRepository repository, RaidHelperHttpClient client,
                                    RaidHelperPayloadRenderer payloads,
                                    TransactionTemplate transactions, Clock clock, RaidHelperDtoMapper mapper) {
        this.repository = repository;
        this.client = client;
        this.payloads = payloads;
        this.transactions = transactions;
        this.clock = clock;
        this.mapper = mapper;
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
            var row = repository.optional(RaidHelperDeliveryQueries.CLAIM_WITH_01, Map.of("now", now()));
            return row.map(value -> longValue(value, "id")).orElse(null);
        });
    }

    private void deliver(long linkId) {
        RaidHelperDeliveryDto link = detail(linkId);
        String operation = link.operation();
        try {
            if (!"delete".equals(operation)
                    && (!link.destinationActive()
                    || !link.profileActive()
                    || !link.templateActive())) {
                throw new RaidHelperHttpClient.RaidHelperTransportException(
                        "Raid-Helper profile, destination or template is inactive.");
            }
            String externalId = link.externalEventId();
            if ("delete".equals(operation) && externalId == null) {
                deleteLink(linkId);
                return;
            }
            RaidHelperHttpClient.Response response;
            if ("delete".equals(operation)) {
                response = client.request(link.connection(), "DELETE", "/events/" + externalId, null);
            } else {
                String leaderId = link.leaderIdOverride();
                if (leaderId == null) leaderId = link.defaultLeaderId();
                if (leaderId == null) {
                    throw new RaidHelperHttpClient.RaidHelperTransportException(
                            "Raid-Helper leader ID is missing for this event.");
                }
                RaidHelperJsonPayloadDto payload = payloads.render(link.event(), link.template(), leaderId);
                if (externalId == null) {
                    String path = "/servers/" + link.serverId()
                            + "/channels/" + link.channelId() + "/event";
                    response = client.request(link.connection(), "POST", path, payload);
                } else {
                    response = client.request(link.connection(), "PATCH", "/events/" + externalId, payload);
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

    private RaidHelperDeliveryDto detail(long linkId) {
        return mapper.delivery(repository.required(RaidHelperDeliveryQueries.DETAIL_SELECT_01, Map.of("id", linkId)));
    }

    private void recoverAbandonedClaims() {
        transactions.executeWithoutResult(status -> repository.update(RaidHelperDeliveryQueries.RECOVER_ABANDONED_CLAIMS_UPDATE_01, Map.of("now", now(), "cutoff", now().minusMinutes(15))));
    }

    private void succeed(long id, String externalId, int responseStatus, String operation) {
        transactions.executeWithoutResult(status -> repository.update(RaidHelperDeliveryQueries.SUCCEED_UPDATE_01, Map.of("externalId", externalId, "responseStatus", responseStatus,
                "operation", operation, "now", now(), "id", id)));
    }

    private void fail(long id, Integer responseStatus, String message) {
        transactions.executeWithoutResult(status -> repository.update(RaidHelperDeliveryQueries.FAIL_UPDATE_01, SqlParameters.ofNullable("responseStatus", responseStatus,
                "message", truncate(message), "now", now(), "id", id)));
    }

    private void deleteLink(long id) {
        transactions.executeWithoutResult(status -> repository.update(
                RaidHelperDeliveryQueries.DELETE_LINK_DELETE_01, Map.of("id", id)));
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
