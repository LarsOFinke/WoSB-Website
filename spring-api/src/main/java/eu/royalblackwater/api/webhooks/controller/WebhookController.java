package eu.royalblackwater.api.webhooks.controller;

import eu.royalblackwater.api.dto.OutboundWebhookDeliveryDeleteResult;
import eu.royalblackwater.api.dto.OutboundWebhookDeliveryRead;
import eu.royalblackwater.api.dto.OutboundWebhookEventCatalogItem;
import eu.royalblackwater.api.dto.OutboundWebhookRead;
import eu.royalblackwater.api.dto.OutboundWebhookSummary;
import java.util.List;
import eu.royalblackwater.api.dto.OutboundWebhookBroadcastRequest;
import eu.royalblackwater.api.dto.OutboundWebhookCreate;
import eu.royalblackwater.api.dto.OutboundWebhookTestRequest;
import eu.royalblackwater.api.dto.OutboundWebhookUpdate;
import eu.royalblackwater.api.contract.api.AdminDiscordWebhooksApi;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.webhooks.model.WebhookEventCatalog;
import eu.royalblackwater.api.webhooks.service.WebhookService;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class WebhookController extends ApiControllerSupport implements AdminDiscordWebhooksApi {

    private final WebhookService webhooks;
    public WebhookController(WebhookService webhooks){this.webhooks=webhooks;}

    @Override
    public ResponseEntity<List<OutboundWebhookRead>> adminListWebhooks(
            String purpose
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.list(purpose), 200);
    }

    @Override
    public ResponseEntity<OutboundWebhookRead> adminCreateWebhook(
            OutboundWebhookCreate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.create(actor,body), 201);
    }

    @Override
    public ResponseEntity<List<OutboundWebhookDeliveryRead>> adminSendBroadcast(
            OutboundWebhookBroadcastRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.broadcast(actor,body), 200);
    }

    @Override
    public ResponseEntity<List<OutboundWebhookRead>> adminListBroadcastWebhooks() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.list("broadcast"), 200);
    }

    @Override
    public ResponseEntity<OutboundWebhookDeliveryDeleteResult> adminDeleteWebhookDeliveryHistory(
            Long webhookId,
            String status,
            String eventType
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.deleteHistory(actor,
                            webhookId,status,eventType), 200);
    }

    @Override
    public ResponseEntity<List<OutboundWebhookDeliveryRead>> adminListWebhookDeliveries(
            Long webhookId,
            String status,
            String eventType,
            long limit
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.deliveries(
                            webhookId,status,eventType,limit), 200);
    }

    @Override
    public ResponseEntity<OutboundWebhookDeliveryDeleteResult> adminDeleteWebhookDelivery(
            long deliveryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.deleteDelivery(actor,deliveryId), 200);
    }

    @Override
    public ResponseEntity<OutboundWebhookDeliveryRead> adminRetryWebhookDelivery(
            long deliveryId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.retry(actor,deliveryId), 200);
    }

    @Override
    public ResponseEntity<List<OutboundWebhookEventCatalogItem>> adminWebhookEventCatalog() {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(WebhookEventCatalog.ALL, 200);
    }

    @Override
    public ResponseEntity<OutboundWebhookSummary> adminWebhookSummary(
            String purpose
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.summary(purpose), 200);
    }

    @Override
    public ResponseEntity<Void> adminDeleteWebhook(
            long webhookId
    ) {

        AuthenticatedUser actor=CurrentUser.require();
        webhooks.delete(actor,webhookId);return noContent();
    }

    @Override
    public ResponseEntity<OutboundWebhookRead> adminUpdateWebhook(
            long webhookId,
            OutboundWebhookUpdate body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.update(actor,webhookId,body), 200);
    }

    @Override
    public ResponseEntity<OutboundWebhookDeliveryRead> adminTestWebhook(
            long webhookId,
            OutboundWebhookTestRequest body
    ) {
        AuthenticatedUser actor=CurrentUser.require();
        return respond(webhooks.test(actor,webhookId,body), 200);
    }
    private static Long nullableLong(Map<String,Object> parameters,String name){Object value=parameters.get(name);return value instanceof Number number?number.longValue():null;}
}
