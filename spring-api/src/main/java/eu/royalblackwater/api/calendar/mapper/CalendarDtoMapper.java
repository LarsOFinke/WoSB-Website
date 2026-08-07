package eu.royalblackwater.api.calendar.mapper;

import eu.royalblackwater.api.dto.CalendarSquadRead;
import eu.royalblackwater.api.dto.FleetEventRead;
import eu.royalblackwater.api.dto.RaidHelperEventLinkRead;
import eu.royalblackwater.api.dto.UserReferenceRead;
import java.util.List;
import java.util.Map;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.nullableLong;
import static eu.royalblackwater.api.persistence.RowValues.string;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.persistence.RowValues.booleanValue;
import static eu.royalblackwater.api.persistence.RowValues.dateTime;

public final class CalendarDtoMapper {
    private CalendarDtoMapper() { }

    public static FleetEventRead event(
            Map<String, Object> row, boolean canManage, Map<Long, List<RaidHelperEventLinkRead>> links) {
        Long squadId = nullableLong(row, "squad_id");
        CalendarSquadRead squad = squadId == null ? null : new CalendarSquadRead(
                squadId, requiredString(row, "squad_name"), requiredString(row, "squad_slug"));
        long eventId = longValue(row, "id");
        return new FleetEventRead(booleanValue(row, "all_day"), canManage,
                requiredString(row, "category"), dateTime(row, "created_at"), string(row, "description"),
                dateTime(row, "end_at"), eventId, booleanValue(row, "is_cancelled"), string(row, "location"),
                new UserReferenceRead(requiredString(row, "owner_display_name"), longValue(row, "owner_id")),
                longValue(row, "owner_id"), booleanValue(row, "raid_helper_enabled"),
                canManage ? links.getOrDefault(eventId, List.of()) : List.of(),
                squadId == null ? "Fleet" : requiredString(row, "squad_name"),
                squadId == null ? "fleet" : "squad", squad, squadId, dateTime(row, "start_at"),
                requiredString(row, "title"), dateTime(row, "updated_at"));
    }
}
