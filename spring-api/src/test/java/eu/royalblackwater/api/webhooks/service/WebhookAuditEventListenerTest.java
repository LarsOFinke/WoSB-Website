package eu.royalblackwater.api.webhooks.service;

import eu.royalblackwater.api.audit.dto.AuditRecordedEvent;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class WebhookAuditEventListenerTest {
    private static final AuthenticatedUser ACTOR =
            new AuthenticatedUser(1, "admin", "admin", true, true, true);

    @Test
    void mapsAuditedActionsAndPreservesFleetScope() {
        AuditRecordedEvent audit = audit("fleet", "44", "create", "Fleet created.");

        var event = WebhookAuditEventListener.map(audit).orElseThrow();

        assertThat(event.eventType()).isEqualTo("fleet.created");
        assertThat(event.scopeType()).isEqualTo("fleet");
        assertThat(event.scopeId()).isEqualTo(44L);
    }

    @Test
    void distinguishesRegistrationDecisionsAndIgnoresUnrelatedAudits() {
        assertThat(WebhookAuditEventListener.map(audit("registration_request", "7", "update",
                "Access request approved.")).orElseThrow().eventType()).isEqualTo("registration.request.approved");
        assertThat(WebhookAuditEventListener.map(audit("registration_request", "8", "update",
                "Access request rejected.")).orElseThrow().eventType()).isEqualTo("registration.request.rejected");
        assertThat(WebhookAuditEventListener.map(audit("outbound_webhook", "9", "create",
                "Webhook created."))).isEmpty();
    }

    @Test
    void mapsWarehouseStockAndReservationActions() {
        assertThat(WebhookAuditEventListener.map(audit("warehouse_entry", "41", "update",
                "Warehouse stock updated.")).orElseThrow().eventType()).isEqualTo("warehouse.stock.changed");
        assertThat(WebhookAuditEventListener.map(audit("warehouse_entry", "41", "reservation",
                "Warehouse reservation changed.")).orElseThrow().eventType())
                .isEqualTo("warehouse.reservation.changed");
    }

    private static AuditRecordedEvent audit(String type, String id, String action, String summary) {
        String scopeType = "fleet".equals(type) ? "fleet" : null;
        Long scopeId = scopeType == null ? null : Long.valueOf(id);
        return new AuditRecordedEvent(action, ACTOR, id, type,
                LocalDateTime.of(2026, 8, 9, 20, 0), scopeId, scopeType, summary);
    }
}
