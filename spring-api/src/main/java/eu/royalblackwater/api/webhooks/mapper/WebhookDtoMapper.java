package eu.royalblackwater.api.webhooks.mapper;

import eu.royalblackwater.api.dto.OutboundWebhookDeliveryDeleteResult;
import eu.royalblackwater.api.dto.OutboundWebhookDeliveryRead;
import eu.royalblackwater.api.dto.OutboundWebhookEventCatalogItem;
import eu.royalblackwater.api.dto.OutboundWebhookRead;
import eu.royalblackwater.api.dto.OutboundWebhookSummary;
import eu.royalblackwater.api.shared.mapper.ContractConversionService;
import eu.royalblackwater.api.webhooks.dto.WebhookEventDefinition;
import java.util.List;
import java.util.Map;

import static eu.royalblackwater.api.persistence.RowValues.*;

public final class WebhookDtoMapper {
    private WebhookDtoMapper() { }

    public static OutboundWebhookRead webhook(
            Map<String, Object> row, String publicEndpoint, List<String> events) {
        return new OutboundWebhookRead(booleanValue(row, "broadcast_enabled"), dateTime(row, "created_at"),
                requiredString(row, "created_by_username"), string(row, "discord_username"), publicEndpoint,
                events, longValue(row, "id"), booleanValue(row, "is_active"),
                nullableDateTime(row, "last_failure_at"), nullableDateTime(row, "last_success_at"),
                string(row, "message_template"), requiredString(row, "name"), nullableLong(row, "scope_id"),
                requiredString(row, "scope_type"), dateTime(row, "updated_at"));
    }
    public static OutboundWebhookSummary summary(long active, long failures, long scoped,
            long deliveries, long broadcastTargets) {
        return new OutboundWebhookSummary(active, failures, scoped, deliveries, broadcastTargets);
    }

    public static OutboundWebhookDeliveryRead delivery(Map<String, Object> row,
            ContractConversionService contracts) {
        return contracts.convert(row, OutboundWebhookDeliveryRead.class);
    }

    public static List<OutboundWebhookEventCatalogItem> eventCatalog(List<WebhookEventDefinition> definitions) {
        return definitions.stream()
                .map(definition -> new OutboundWebhookEventCatalogItem(
                        definition.defaultTemplate(), definition.description(),
                        definition.group(), definition.key()))
                .toList();
    }

    public static OutboundWebhookDeliveryDeleteResult deleted(long count) {
        return new OutboundWebhookDeliveryDeleteResult(count);
    }

}
