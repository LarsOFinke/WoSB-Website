package eu.royalblackwater.api.warehouse.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.webhooks.dto.WebhookDomainEvent;
import eu.royalblackwater.api.webhooks.service.WebhookService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.NOT_FOUND;
import static org.springframework.http.HttpStatus.FORBIDDEN;

/** Publishes a manually requested, fleet-scoped warehouse snapshot. */
@Service
public class WarehouseOverviewWebhookService {
    private final WarehouseOverviewService overview;
    private final WarehousePortAssignmentService access;
    private final WebhookService webhooks;
    private final AuditService audit;
    private final Clock clock;

    public WarehouseOverviewWebhookService(WarehouseOverviewService overview,
                                           WarehousePortAssignmentService access,
                                           WebhookService webhooks, AuditService audit, Clock clock) {
        this.overview = overview;
        this.access = access;
        this.webhooks = webhooks;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional
    public void publish(long fleetId, AuthenticatedUser actor) {
        if (fleetId < 1) throw new ResponseStatusException(NOT_FOUND, "Fleet not found.");
        if (actor == null || !actor.staff()) {
            throw new ResponseStatusException(FORBIDDEN, "Warehouse overview publishing requires staff access.");
        }
        access.requireStaffFleet(fleetId);
        String summary = overview.format(overview.overview(fleetId));
        LocalDateTime now = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        audit.record(actor, "warehouse_overview_webhook", String.valueOf(fleetId), "publish",
                "Published warehouse stock overview", List.of("fleet_id"), "fleet", fleetId);
        webhooks.publish(new WebhookDomainEvent("warehouse.stock.overview", "warehouse",
                String.valueOf(fleetId), "fleet", fleetId, actor, summary, now));
    }
}
