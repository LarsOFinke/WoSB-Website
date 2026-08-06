package eu.royalblackwater.api.groups.mapper;

import eu.royalblackwater.api.dto.GroupMemberRead;
import eu.royalblackwater.api.dto.GroupRead;
import eu.royalblackwater.api.dto.ShipRead;
import eu.royalblackwater.api.dto.UserReferenceRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

public final class GroupDtoMapper {
    private GroupDtoMapper() { }

    public static GroupRead group(Map<String, Object> row, List<GroupMemberRead> members,
                                  String status, boolean joinable) {
        long id = RowValues.longValue(row, "id");
        long active = RowValues.longValue(row, "active_count");
        long max = RowValues.longValue(row, "max_members");
        return new GroupRead(active, RowValues.string(row, "activity_plan"),
                RowValues.booleanValue(row, "allow_guests"), RowValues.nullableDateTime(row, "closed_at"),
                RowValues.string(row, "contact_note"), RowValues.dateTime(row, "created_at"),
                RowValues.string(row, "description"), RowValues.string(row, "expectations"),
                RowValues.dateTime(row, "expires_at"), RowValues.string(row, "fleet_restriction"),
                RowValues.string(row, "focus"), id, joinable, max, RowValues.nullableLong(row, "max_ship_rate"),
                members, RowValues.nullableLong(row, "min_ship_rate"),
                new UserReferenceRead(RowValues.requiredString(row, "owner_display_name"),
                        RowValues.longValue(row, "owner_id")),
                RowValues.longValue(row, "owner_id"), RowValues.nullableDateTime(row, "scheduled_end_at"),
                RowValues.nullableDateTime(row, "scheduled_start_at"), Math.max(0, max - active), status,
                RowValues.requiredString(row, "title"), RowValues.dateTime(row, "updated_at"));
    }

    public static GroupMemberRead member(Map<String, Object> row, ShipRead ship) {
        Long shipId = RowValues.nullableLong(row, "ship_id");
        return new GroupMemberRead(null, RowValues.nullableLong(row, "build_id"),
                RowValues.requiredString(row, "display_name"), RowValues.string(row, "fleet_name"),
                RowValues.longValue(row, "id"), RowValues.booleanValue(row, "is_active"),
                RowValues.booleanValue(row, "is_guest"), RowValues.dateTime(row, "joined_at"),
                RowValues.nullableDateTime(row, "left_at"), RowValues.string(row, "note"), ship, shipId,
                RowValues.string(row, "ship_name"), RowValues.nullableLong(row, "ship_rate"),
                RowValues.nullableLong(row, "user_id"));
    }
}
