package eu.royalblackwater.api.squads.mapper;

import eu.royalblackwater.api.dto.SquadDetailRead;
import eu.royalblackwater.api.dto.SquadMemberRead;
import eu.royalblackwater.api.dto.SquadRosterMemberRead;
import eu.royalblackwater.api.dto.SquadSummaryRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

public final class SquadDtoMapper {
    private SquadDtoMapper() { }

    public static SquadRosterMemberRead roster(Map<String, Object> row, List<Long> squadIds) {
        return new SquadRosterMemberRead(RowValues.requiredString(row, "display_name"),
                RowValues.longValue(row, "fleet_membership_id"), RowValues.requiredString(row, "fleet_role"),
                squadIds, RowValues.longValue(row, "user_id"));
    }

    public static SquadMemberRead member(Map<String, Object> row, boolean includeNote) {
        return new SquadMemberRead(RowValues.requiredString(row, "display_name"),
                RowValues.longValue(row, "fleet_membership_id"), RowValues.requiredString(row, "fleet_role"),
                RowValues.longValue(row, "id"), RowValues.dateTime(row, "joined_at"),
                includeNote ? RowValues.string(row, "note") : null,
                RowValues.requiredString(row, "squad_role"), RowValues.longValue(row, "user_id"));
    }

    public static SquadSummaryRead summary(Map<String, Object> row, String currentRole,
                                           boolean member, boolean manage, boolean administer,
                                           SquadMemberRead leader, long memberCount) {
        return new SquadSummaryRead(administer, manage, RowValues.dateTime(row, "created_at"), currentRole,
                RowValues.string(row, "description"), RowValues.longValue(row, "fleet_id"),
                RowValues.string(row, "focus"), RowValues.longValue(row, "id"),
                RowValues.booleanValue(row, "is_active"), member, leader,
                RowValues.nullableLong(row, "max_members"), memberCount,
                RowValues.requiredString(row, "name"), RowValues.requiredString(row, "slug"),
                RowValues.dateTime(row, "updated_at"));
    }

    public static SquadDetailRead detail(SquadSummaryRead summary, List<SquadMemberRead> members) {
        return new SquadDetailRead(summary.canAdminister(), summary.canManage(), summary.createdAt(),
                summary.currentUserRole(), summary.description(), summary.fleetId(), summary.focus(), summary.id(),
                summary.isActive(), summary.isMember(), summary.leader(), summary.maxMembers(),
                summary.memberCount(), members, summary.name(), summary.slug(), summary.updatedAt());
    }
}
