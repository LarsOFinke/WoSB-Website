package eu.royalblackwater.api.webhooks;

import eu.royalblackwater.api.contract.*;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class WebhookOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS=Set.of(
            "admin_list_webhooks_api_admin_discord_webhooks_get","admin_create_webhook_api_admin_discord_webhooks_post",
            "admin_send_broadcast_api_admin_discord_webhooks_broadcast_send_post","admin_list_broadcast_webhooks_api_admin_discord_webhooks_broadcast_targets_get",
            "admin_delete_webhook_delivery_history_api_admin_discord_webhooks_deliveries_history_delete",
            "admin_list_webhook_deliveries_api_admin_discord_webhooks_deliveries_history_get",
            "admin_delete_webhook_delivery_api_admin_discord_webhooks_deliveries__delivery_id__delete",
            "admin_retry_webhook_delivery_api_admin_discord_webhooks_deliveries__delivery_id__retry_post",
            "admin_webhook_event_catalog_api_admin_discord_webhooks_events_get","admin_webhook_summary_api_admin_discord_webhooks_summary_get",
            "admin_delete_webhook_api_admin_discord_webhooks__webhook_id__delete","admin_update_webhook_api_admin_discord_webhooks__webhook_id__put",
            "admin_test_webhook_api_admin_discord_webhooks__webhook_id__test_post");
    private final WebhookService webhooks;
    public WebhookOperationHandler(WebhookService webhooks){this.webhooks=webhooks;}
    @Override public Set<String> operations(){return OPERATIONS;}

    @Override protected Object execute(String operationId,Map<String,Object> parameters,Object request,MultipartFile upload){
        AuthenticatedUser actor=CurrentUser.require();
        return switch(operationId){
            case "admin_list_webhooks_api_admin_discord_webhooks_get" -> webhooks.list(stringParameter(parameters,"purpose"));
            case "admin_create_webhook_api_admin_discord_webhooks_post" -> webhooks.create(actor,body(request,OutboundWebhookCreate.class));
            case "admin_send_broadcast_api_admin_discord_webhooks_broadcast_send_post" -> webhooks.broadcast(actor,body(request,OutboundWebhookBroadcastRequest.class));
            case "admin_list_broadcast_webhooks_api_admin_discord_webhooks_broadcast_targets_get" -> webhooks.list("broadcast");
            case "admin_delete_webhook_delivery_history_api_admin_discord_webhooks_deliveries_history_delete" -> webhooks.deleteHistory(actor,
                    nullableLong(parameters,"webhook_id"),stringParameter(parameters,"status"),stringParameter(parameters,"event_type"));
            case "admin_list_webhook_deliveries_api_admin_discord_webhooks_deliveries_history_get" -> webhooks.deliveries(
                    nullableLong(parameters,"webhook_id"),stringParameter(parameters,"status"),stringParameter(parameters,"event_type"),longParameter(parameters,"limit"));
            case "admin_delete_webhook_delivery_api_admin_discord_webhooks_deliveries__delivery_id__delete" -> webhooks.deleteDelivery(actor,longParameter(parameters,"delivery_id"));
            case "admin_retry_webhook_delivery_api_admin_discord_webhooks_deliveries__delivery_id__retry_post" -> webhooks.retry(actor,longParameter(parameters,"delivery_id"));
            case "admin_webhook_event_catalog_api_admin_discord_webhooks_events_get" -> WebhookEventCatalog.ALL;
            case "admin_webhook_summary_api_admin_discord_webhooks_summary_get" -> webhooks.summary(stringParameter(parameters,"purpose"));
            case "admin_delete_webhook_api_admin_discord_webhooks__webhook_id__delete" -> {webhooks.delete(actor,longParameter(parameters,"webhook_id"));yield null;}
            case "admin_update_webhook_api_admin_discord_webhooks__webhook_id__put" -> webhooks.update(actor,longParameter(parameters,"webhook_id"),body(request,OutboundWebhookUpdate.class));
            case "admin_test_webhook_api_admin_discord_webhooks__webhook_id__test_post" -> webhooks.test(actor,longParameter(parameters,"webhook_id"),body(request,OutboundWebhookTestRequest.class));
            default -> throw new IllegalArgumentException("Unsupported webhook operation: "+operationId);
        };
    }
    private static Long nullableLong(Map<String,Object> parameters,String name){Object value=parameters.get(name);return value instanceof Number number?number.longValue():null;}
}
