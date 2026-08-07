package eu.royalblackwater.api.raidhelper.mapper;

import eu.royalblackwater.api.dto.RaidHelperDestinationRead;
import eu.royalblackwater.api.dto.RaidHelperProfileRead;
import eu.royalblackwater.api.dto.RaidHelperProfileTestResult;
import eu.royalblackwater.api.dto.RaidHelperEventLinkRead;
import eu.royalblackwater.api.dto.RaidHelperOptionDestination;
import eu.royalblackwater.api.dto.RaidHelperOptionTemplate;
import eu.royalblackwater.api.dto.RaidHelperTemplateRead;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperConnectionDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperDestinationConfigDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperDeliveryDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperEventDto;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperTemplateConfigDto;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.nullableLong;
import static eu.royalblackwater.api.persistence.RowValues.string;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.persistence.RowValues.booleanValue;
import static eu.royalblackwater.api.persistence.RowValues.dateTime;
import static eu.royalblackwater.api.persistence.RowValues.nullableDateTime;

@Component
public class RaidHelperDtoMapper {
    public RaidHelperProfileRead profileRead(Map<String, Object> row) {
        return new RaidHelperProfileRead(requiredString(row, "api_base_url"),
                !requiredString(row, "api_key_encrypted").isBlank(), dateTime(row, "created_at"),
                requiredString(row, "created_by_username"), string(row, "default_leader_id"),
                longValue(row, "id"), booleanValue(row, "is_active"), requiredString(row, "name"),
                requiredString(row, "server_id"), requiredString(row, "timezone"), dateTime(row, "updated_at"));
    }

    public RaidHelperConnectionDto connection(Map<String, Object> row) {
        return new RaidHelperConnectionDto(requiredString(row, "api_base_url"),
                requiredString(row, "api_key_encrypted"), requiredString(row, "server_id"));
    }

    public RaidHelperDestinationRead destinationRead(Map<String, Object> row, List<String> categories) {
        return new RaidHelperDestinationRead(categories, requiredString(row, "channel_id"),
                dateTime(row, "created_at"), longValue(row, "id"), booleanValue(row, "is_active"),
                booleanValue(row, "is_default"), requiredString(row, "name"),
                longValue(row, "profile_id"), requiredString(row, "profile_name"),
                requiredString(row, "scope_type"), nullableLong(row, "squad_id"),
                string(row, "squad_name"), dateTime(row, "updated_at"));
    }

    public RaidHelperDestinationConfigDto destinationConfig(Map<String, Object> row) {
        return new RaidHelperDestinationConfigDto(longValue(row, "id"), longValue(row, "profile_id"),
                requiredString(row, "channel_id"), connection(row), requiredString(row, "timezone"),
                string(row, "default_leader_id"), nullableLong(row, "squad_id"), string(row, "squad_name"));
    }

    public RaidHelperEventDto event(Map<String, Object> row) {
        return new RaidHelperEventDto(longValue(row, "event_id"), requiredString(row, "title"),
                requiredString(row, "category"), string(row, "description"), string(row, "location"),
                dateTime(row, "start_at"), dateTime(row, "end_at"), booleanValue(row, "all_day"),
                nullableLong(row, "squad_id"), string(row, "squad_name"));
    }

    public RaidHelperDeliveryDto delivery(Map<String, Object> row) {
        RaidHelperTemplateConfigDto template = templateConfig(row, requiredString(row, "timezone"));
        return new RaidHelperDeliveryDto(longValue(row, "id"), requiredString(row, "last_operation"),
                string(row, "external_event_id"), string(row, "leader_id_override"),
                string(row, "default_leader_id"), requiredString(row, "server_id"),
                requiredString(row, "channel_id"), booleanValue(row, "destination_active"),
                booleanValue(row, "profile_active"), booleanValue(row, "template_active"),
                connection(row), event(row), template);
    }

    public RaidHelperTemplateRead templateRead(Map<String, Object> row, List<String> categories) {
        return new RaidHelperTemplateRead(requiredString(row, "announcement_template"), categories,
                dateTime(row, "created_at"), requiredString(row, "description_template"), longValue(row, "id"),
                booleanValue(row, "is_active"), booleanValue(row, "is_default"), requiredString(row, "name"),
                requiredString(row, "payload_template_json"), longValue(row, "profile_id"),
                requiredString(row, "profile_name"), requiredString(row, "raid_template_id"),
                requiredString(row, "scope_type"), requiredString(row, "title_template"),
                dateTime(row, "updated_at"), booleanValue(row, "uses_premium_features"));
    }

    public RaidHelperTemplateConfigDto templateConfig(Map<String, Object> row, String timezone) {
        return new RaidHelperTemplateConfigDto(longValue(row, "id"), longValue(row, "profile_id"),
                booleanValue(row, "is_active"), timezone, string(row, "raid_template_id"),
                requiredString(row, "title_template"), requiredString(row, "description_template"),
                requiredString(row, "announcement_template"), requiredString(row, "payload_template_json"));
    }
    public RaidHelperOptionTemplate optionTemplate(Map<String, Object> row) {
        return new RaidHelperOptionTemplate(longValue(row, "template_id"),
                booleanValue(row, "template_default"), requiredString(row, "template_name"),
                longValue(row, "profile_id"), requiredString(row, "profile_name"),
                requiredString(row, "raid_template_id"));
    }

    public RaidHelperOptionDestination optionDestination(long id, String name, long profileId,
            String profileName, String scopeType, Long squadId, boolean isDefault,
            String defaultLeaderId, List<RaidHelperOptionTemplate> templates) {
        return new RaidHelperOptionDestination(defaultLeaderId, id, isDefault, name, profileId,
                profileName, scopeType, squadId, List.copyOf(templates));
    }

    public RaidHelperEventLinkRead eventLink(Map<String, Object> row) {
        return new RaidHelperEventLinkRead(longValue(row, "destination_id"),
                requiredString(row, "destination_name"), string(row, "error_message"),
                string(row, "external_event_id"), longValue(row, "id"),
                requiredString(row, "last_operation"), requiredString(row, "profile_name"),
                requiredString(row, "status"), nullableDateTime(row, "synced_at"),
                longValue(row, "template_id"), requiredString(row, "template_name"));
    }

    public RaidHelperProfileTestResult profileTestResult(boolean ok, Integer status, String message) {
        return new RaidHelperProfileTestResult(message, ok, status == null ? null : status.longValue());
    }

}
