package eu.royalblackwater.api.webhooks.controller;

import eu.royalblackwater.api.dto.OutboundWebhookBroadcastRequest;
import eu.royalblackwater.api.dto.OutboundWebhookCreate;
import eu.royalblackwater.api.dto.OutboundWebhookDeliveryDeleteResult;
import eu.royalblackwater.api.dto.OutboundWebhookDeliveryRead;
import eu.royalblackwater.api.dto.OutboundWebhookEventCatalogItem;
import eu.royalblackwater.api.dto.OutboundWebhookRead;
import eu.royalblackwater.api.dto.OutboundWebhookSummary;
import eu.royalblackwater.api.dto.OutboundWebhookTestRequest;
import eu.royalblackwater.api.dto.OutboundWebhookUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.webhooks.service.WebhookService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class WebhookController extends ApiControllerSupport {

    private final WebhookService webhooks;
    public WebhookController(WebhookService webhooks){this.webhooks=webhooks;}

    @GetMapping("/api/admin/discord-webhooks")
    public ResponseEntity<List<OutboundWebhookRead>> adminListWebhooks(
            @RequestParam(name = "purpose", required = false) String purpose
    ) {

        CurrentUser.require();
        return respond(webhooks.list(purpose), 200);
    }

    @PostMapping("/api/admin/discord-webhooks")
    public ResponseEntity<OutboundWebhookRead> adminCreateWebhook(
            @Valid @RequestBody OutboundWebhookCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.create(actor,body), 201);
    }

    @PostMapping("/api/admin/discord-webhooks/broadcast/send")
    public ResponseEntity<List<OutboundWebhookDeliveryRead>> adminSendBroadcast(
            @Valid @RequestBody OutboundWebhookBroadcastRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.broadcast(actor,body), 200);
    }

    @GetMapping("/api/admin/discord-webhooks/broadcast/targets")
    public ResponseEntity<List<OutboundWebhookRead>> adminListBroadcastWebhooks() {
        CurrentUser.require();
        return respond(webhooks.list("broadcast"), 200);
    }

    @DeleteMapping("/api/admin/discord-webhooks/deliveries/history")
    public ResponseEntity<OutboundWebhookDeliveryDeleteResult> adminDeleteWebhookDeliveryHistory(
            @RequestParam(name = "webhook_id", required = false) Long webhookId,
            @RequestParam(name = "status", required = false) String status,
            @RequestParam(name = "event_type", required = false) String eventType
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.deleteHistory(actor,
                            webhookId,status,eventType), 200);
    }

    @GetMapping("/api/admin/discord-webhooks/deliveries/history")
    public ResponseEntity<List<OutboundWebhookDeliveryRead>> adminListWebhookDeliveries(
            @RequestParam(name = "webhook_id", required = false) Long webhookId,
            @RequestParam(name = "status", required = false) String status,
            @RequestParam(name = "event_type", required = false) String eventType,
            @RequestParam(name = "limit", defaultValue = "100") long limit
    ) {

        CurrentUser.require();
        return respond(webhooks.deliveries(
                            webhookId,status,eventType,limit), 200);
    }

    @DeleteMapping("/api/admin/discord-webhooks/deliveries/{delivery_id}")
    public ResponseEntity<OutboundWebhookDeliveryDeleteResult> adminDeleteWebhookDelivery(
            @PathVariable("delivery_id") long deliveryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.deleteDelivery(actor,deliveryId), 200);
    }

    @PostMapping("/api/admin/discord-webhooks/deliveries/{delivery_id}/retry")
    public ResponseEntity<OutboundWebhookDeliveryRead> adminRetryWebhookDelivery(
            @PathVariable("delivery_id") long deliveryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.retry(actor,deliveryId), 200);
    }

    @GetMapping("/api/admin/discord-webhooks/events")
    public ResponseEntity<List<OutboundWebhookEventCatalogItem>> adminWebhookEventCatalog() {
        CurrentUser.require();
        return respond(webhooks.eventCatalog(), 200);
    }

    @GetMapping("/api/admin/discord-webhooks/summary")
    public ResponseEntity<OutboundWebhookSummary> adminWebhookSummary(
            @RequestParam(name = "purpose", required = false) String purpose
    ) {

        CurrentUser.require();
        return respond(webhooks.summary(purpose), 200);
    }

    @DeleteMapping("/api/admin/discord-webhooks/{webhook_id}")
    public ResponseEntity<Void> adminDeleteWebhook(
            @PathVariable("webhook_id") long webhookId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        webhooks.delete(actor,webhookId);return noContent();
    }

    @PutMapping("/api/admin/discord-webhooks/{webhook_id}")
    public ResponseEntity<OutboundWebhookRead> adminUpdateWebhook(
            @PathVariable("webhook_id") long webhookId,
            @Valid @RequestBody OutboundWebhookUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.update(actor,webhookId,body), 200);
    }

    @PostMapping("/api/admin/discord-webhooks/{webhook_id}/test")
    public ResponseEntity<OutboundWebhookDeliveryRead> adminTestWebhook(
            @PathVariable("webhook_id") long webhookId,
            @Valid @RequestBody OutboundWebhookTestRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.test(actor,webhookId,body), 200);
    }
}
