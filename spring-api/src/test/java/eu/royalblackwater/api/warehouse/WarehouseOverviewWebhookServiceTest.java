package eu.royalblackwater.api.warehouse;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.webhooks.service.WebhookService;
import eu.royalblackwater.api.warehouse.dto.WarehouseStockOverview;
import eu.royalblackwater.api.warehouse.service.WarehouseOverviewService;
import eu.royalblackwater.api.warehouse.service.WarehouseOverviewWebhookService;
import eu.royalblackwater.api.warehouse.service.WarehousePortAssignmentService;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class WarehouseOverviewWebhookServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser MODERATOR =
            new AuthenticatedUser(7, "moderator", "moderator", true, false, false);

    @Test
    void publishesCurrentFleetOverviewThroughConfiguredWebhookSubscriptions() {
        WarehouseOverviewService overview = mock(WarehouseOverviewService.class);
        WarehousePortAssignmentService access = mock(WarehousePortAssignmentService.class);
        WebhookService webhooks = mock(WebhookService.class);
        AuditService audit = mock(AuditService.class);
        WarehouseStockOverview stock = new WarehouseStockOverview("Blackwater", 1250, 1000, 250,
                List.of(new WarehouseStockOverview.Line("Nassau", "Iron", 1250, 1000, 250)));
        when(overview.overview(4L)).thenReturn(stock);
        when(overview.format(stock)).thenReturn("Fleet: Blackwater\nTotal: 1250");

        new WarehouseOverviewWebhookService(overview, access, webhooks, audit, CLOCK).publish(4L, MODERATOR);

        verify(access).requireStaffFleet(4L);
        verify(webhooks).publish(any());
        verify(audit).record(eq(MODERATOR), eq("warehouse_overview_webhook"), eq("4"), eq("publish"),
                eq("Published warehouse stock overview"), eq(List.of("fleet_id")), eq("fleet"), eq(4L));
    }
}
