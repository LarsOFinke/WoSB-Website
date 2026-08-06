package eu.royalblackwater.api.audit.mapper;

import eu.royalblackwater.api.dto.AuditLogRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

public final class AuditDtoMapper {
    private AuditDtoMapper() { }

    public static AuditLogRead toRead(Map<String, Object> row, List<String> changedFields) {
        return new AuditLogRead(RowValues.requiredString(row, "action"),
                RowValues.requiredString(row, "actor_role"), RowValues.nullableLong(row, "actor_user_id"),
                RowValues.requiredString(row, "actor_username"), changedFields,
                RowValues.dateTime(row, "created_at"), RowValues.requiredString(row, "entity_id"),
                RowValues.requiredString(row, "entity_type"), RowValues.longValue(row, "id"),
                RowValues.requiredString(row, "summary"));
    }
}
