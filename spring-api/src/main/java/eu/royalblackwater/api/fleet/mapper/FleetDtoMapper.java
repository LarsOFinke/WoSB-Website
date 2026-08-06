package eu.royalblackwater.api.fleet.mapper;

import eu.royalblackwater.api.dto.FleetDetail;
import eu.royalblackwater.api.dto.FleetMemberUserRead;
import eu.royalblackwater.api.dto.FleetMembershipFleetRead;
import eu.royalblackwater.api.dto.FleetMembershipManagementRead;
import eu.royalblackwater.api.dto.FleetMembershipRead;
import eu.royalblackwater.api.dto.FleetMembershipSelfRead;
import eu.royalblackwater.api.dto.FleetMembershipUpdate;
import eu.royalblackwater.api.dto.FleetPublicLeaderRead;
import eu.royalblackwater.api.dto.FleetPublicRead;
import eu.royalblackwater.api.dto.FleetRead;
import eu.royalblackwater.api.dto.FleetRoleRead;
import eu.royalblackwater.api.fleet.dto.FleetMembershipTargetDto;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class FleetDtoMapper {
    public FleetMembershipUpdate membershipUpdate(FleetMembershipUpdate source, String role, String status) {
        return new FleetMembershipUpdate(source.adminNote(), source.assignment(), source.note(), role, status);
    }

    public FleetMembershipTargetDto membershipTarget(Map<String, Object> row) {
        return new FleetMembershipTargetDto(
                RowValues.longValue(row, "user_id"), RowValues.requiredString(row, "role"),
                RowValues.longValue(row, "role_rank"), RowValues.requiredString(row, "status"),
                RowValues.requiredString(row, "site_role"));
    }

    public FleetRoleRead role(Map<String, Object> row) {
        return new FleetRoleRead(RowValues.booleanValue(row, "can_manage_fleet"),
                RowValues.booleanValue(row, "can_manage_members"), RowValues.requiredString(row, "code"),
                RowValues.longValue(row, "id"), RowValues.booleanValue(row, "is_active"),
                RowValues.booleanValue(row, "is_leadership"), RowValues.booleanValue(row, "is_system"),
                RowValues.requiredString(row, "label"), RowValues.nullableLong(row, "member_count"),
                RowValues.longValue(row, "rank"));
    }

    public FleetPublicLeaderRead publicLeader(Map<String, Object> row) {
        return new FleetPublicLeaderRead(RowValues.requiredString(row, "display_name"),
                RowValues.requiredString(row, "role"), RowValues.requiredString(row, "role_label"));
    }

    public FleetPublicRead publicFleet(Map<String, Object> row, List<FleetPublicLeaderRead> leaders) {
        return new FleetPublicRead(RowValues.nullableLong(row, "active_count"),
                RowValues.string(row, "description"), RowValues.requiredString(row, "focus"),
                RowValues.longValue(row, "id"), leaders, RowValues.requiredString(row, "name"),
                RowValues.requiredString(row, "slug"), RowValues.string(row, "standing_orders"));
    }

    public FleetRead fleet(Map<String, Object> row, List<FleetMembershipRead> leaders) {
        return new FleetRead(RowValues.nullableLong(row, "active_count"), RowValues.dateTime(row, "created_at"),
                RowValues.string(row, "description"), RowValues.requiredString(row, "focus"),
                RowValues.longValue(row, "id"), RowValues.booleanValue(row, "is_active"), leaders,
                RowValues.requiredString(row, "name"), RowValues.nullableLong(row, "pending_count"),
                RowValues.requiredString(row, "slug"), RowValues.longValue(row, "sort_order"),
                RowValues.string(row, "standing_orders"), RowValues.dateTime(row, "updated_at"));
    }

    public FleetDetail detail(Map<String, Object> row, List<FleetMembershipRead> leaders,
                              List<FleetMembershipRead> memberships) {
        return new FleetDetail(RowValues.nullableLong(row, "active_count"),
                RowValues.dateTime(row, "created_at"), RowValues.string(row, "description"),
                RowValues.requiredString(row, "focus"), RowValues.longValue(row, "id"),
                RowValues.booleanValue(row, "is_active"), leaders, memberships,
                RowValues.requiredString(row, "name"), RowValues.nullableLong(row, "pending_count"),
                RowValues.requiredString(row, "slug"), RowValues.longValue(row, "sort_order"),
                RowValues.string(row, "standing_orders"), RowValues.dateTime(row, "updated_at"));
    }

    public FleetMembershipRead membership(
            Map<String, Object> row, FleetMembershipManagementRead management) {
        FleetMemberUserRead user = new FleetMemberUserRead(RowValues.requiredString(row, "display_name"),
                RowValues.longValue(row, "user_id"), RowValues.requiredString(row, "site_role"),
                RowValues.requiredString(row, "username"));
        return new FleetMembershipRead(RowValues.string(row, "admin_note"), RowValues.string(row, "assignment"),
                RowValues.string(row, "availability"), RowValues.string(row, "discord_handle"),
                RowValues.longValue(row, "fleet_id"), RowValues.longValue(row, "id"),
                RowValues.dateTime(row, "joined_at"), management, RowValues.string(row, "note"),
                RowValues.string(row, "preferred_roles"), RowValues.string(row, "preferred_ships"),
                RowValues.requiredString(row, "role"), RowValues.requiredString(row, "status"),
                RowValues.string(row, "timezone"), RowValues.dateTime(row, "updated_at"), user,
                RowValues.longValue(row, "user_id"));
    }

    public FleetMembershipSelfRead selfMembership(
            Map<String, Object> row, FleetMembershipRead member) {
        FleetMembershipFleetRead fleet = new FleetMembershipFleetRead(
                RowValues.requiredString(row, "fleet_focus"), RowValues.longValue(row, "fleet_id"),
                RowValues.booleanValue(row, "fleet_active"), RowValues.requiredString(row, "fleet_name"),
                RowValues.requiredString(row, "fleet_slug"));
        return new FleetMembershipSelfRead(member.adminNote(), member.assignment(), member.availability(),
                member.discordHandle(), fleet, member.fleetId(), member.id(), member.joinedAt(),
                member.management(), member.note(), member.preferredRoles(), member.preferredShips(), member.role(),
                member.status(), member.timezone(), member.updatedAt(), member.user(), member.userId());
    }
    public static FleetMembershipManagementRead management(boolean edit, boolean role, boolean status,
            List<String> assignable, String reason) {
        return new FleetMembershipManagementRead(assignable, role, status, edit,
                reason != null || !(edit || role || status), reason);
    }

}
