package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.contract.FleetDetail;
import eu.royalblackwater.api.contract.FleetMemberUserRead;
import eu.royalblackwater.api.contract.FleetMembershipFleetRead;
import eu.royalblackwater.api.contract.FleetMembershipRead;
import eu.royalblackwater.api.contract.FleetMembershipSelfRead;
import eu.royalblackwater.api.contract.FleetPublicLeaderRead;
import eu.royalblackwater.api.contract.FleetPublicRead;
import eu.royalblackwater.api.contract.FleetRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class FleetViewService {
    private static final String FLEET_SELECT = """
            select f.*,
                   (select count(*) from fleet_memberships m where m.fleet_id=f.id and m.status='active') active_count,
                   (select count(*) from fleet_memberships m where m.fleet_id=f.id and m.status='pending') pending_count
            from fleets f
            """;
    private static final String MEMBERSHIP_SELECT = """
            select m.*, r.code as role, r.label as role_label, r.rank as role_rank,
                   f.name as fleet_name, f.slug as fleet_slug, f.focus as fleet_focus, f.is_active as fleet_active,
                   u.username, sr.code as site_role, coalesce(up.display_name, u.username) as display_name,
                   up.availability, up.timezone, up.discord_handle,
                   (select string_agg(s.name, ', ' order by p.sort_order, p.id)
                      from user_profile_ship_preferences p join ships s on s.id=p.ship_id
                     where p.user_id=u.id) as preferred_ships,
                   (select string_agg(fr.label, ', ' order by p.sort_order, p.id)
                      from user_profile_role_preferences p join fleet_roles fr on fr.id=p.fleet_role_id
                     where p.user_id=u.id) as preferred_roles
            from fleet_memberships m
            join fleet_roles r on r.id=m.fleet_role_id
            join fleets f on f.id=m.fleet_id
            join users u on u.id=m.user_id
            join site_roles sr on sr.id=u.site_role_id
            left join user_profiles up on up.user_id=u.id
            """;
    private final JdbcQueryService jdbc;
    private final FleetAccessPolicy policy;

    public FleetViewService(JdbcQueryService jdbc, FleetAccessPolicy policy) {
        this.jdbc = jdbc;
        this.policy = policy;
    }

    @Transactional(readOnly = true)
    public FleetPublicRead officialPublic() {
        Map<String, Object> row = official(false);
        List<FleetPublicLeaderRead> leaders = membershipRows(RowValues.longValue(row, "id"), true).stream()
                .map(item -> new FleetPublicLeaderRead(
                        RowValues.requiredString(item, "display_name"),
                        RowValues.requiredString(item, "role"),
                        RowValues.requiredString(item, "role_label")))
                .toList();
        return new FleetPublicRead(
                RowValues.nullableLong(row, "active_count"),
                RowValues.string(row, "description"),
                RowValues.requiredString(row, "focus"),
                RowValues.longValue(row, "id"),
                leaders,
                RowValues.requiredString(row, "name"),
                RowValues.requiredString(row, "slug"),
                RowValues.string(row, "standing_orders"));
    }

    @Transactional(readOnly = true)
    public List<FleetRead> list(boolean includeInactive) {
        Map<String, Object> row = official(includeInactive);
        return List.of(fleetRead(row));
    }

    @Transactional(readOnly = true)
    public List<FleetRead> manageable(AuthenticatedUser actor) {
        Map<String, Object> row = official(actor.staff());
        long fleetId = RowValues.longValue(row, "id");
        if (!policy.canManageFleet(actor, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN, "Fleet leadership access required.");
        }
        return List.of(fleetRead(row));
    }

    @Transactional(readOnly = true)
    public List<FleetMembershipSelfRead> membershipsFor(int userId) {
        return jdbc.query(MEMBERSHIP_SELECT + """
                where m.user_id=:userId
                order by m.status asc, m.joined_at desc
                """, Map.of("userId", userId)).stream().map(this::selfMembership).toList();
    }

    @Transactional(readOnly = true)
    public FleetDetail detail(long fleetId, boolean management, AuthenticatedUser actor) {
        Map<String, Object> row = fleet(fleetId, management);
        if (management) policy.requireFleetManager(actor, fleetId);
        List<FleetMembershipRead> memberships = management
                ? membershipRows(fleetId, false).stream().map(item -> membership(item, actor)).toList()
                : List.of();
        List<FleetMembershipRead> leaders = membershipRows(fleetId, true).stream()
                .map(item -> membership(item, null)).toList();
        return new FleetDetail(
                RowValues.nullableLong(row, "active_count"), RowValues.dateTime(row, "created_at"),
                RowValues.string(row, "description"), RowValues.requiredString(row, "focus"),
                RowValues.longValue(row, "id"), RowValues.booleanValue(row, "is_active"), leaders,
                memberships, RowValues.requiredString(row, "name"), RowValues.nullableLong(row, "pending_count"),
                RowValues.requiredString(row, "slug"), RowValues.longValue(row, "sort_order"),
                RowValues.string(row, "standing_orders"), RowValues.dateTime(row, "updated_at"));
    }

    @Transactional(readOnly = true)
    public FleetRead read(long fleetId, boolean includeInactive) {
        return fleetRead(fleet(fleetId, includeInactive));
    }

    @Transactional(readOnly = true)
    public FleetMembershipRead membership(long membershipId, AuthenticatedUser actor) {
        Map<String, Object> row = jdbc.optional(MEMBERSHIP_SELECT + " where m.id=:id", Map.of("id", membershipId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Membership not found."));
        return membership(row, actor);
    }

    private Map<String, Object> official(boolean includeInactive) {
        String active = includeInactive ? "" : " where f.is_active=true";
        return jdbc.optional(FLEET_SELECT + active + " order by case when f.slug='royal-blackwater-fleet' then 0 else 1 end, f.sort_order, f.id limit 1",
                Map.of()).orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Fleet not found."));
    }

    private Map<String, Object> fleet(long fleetId, boolean includeInactive) {
        String active = includeInactive ? "" : " and f.is_active=true";
        return jdbc.optional(FLEET_SELECT + " where f.id=:id" + active, Map.of("id", fleetId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Fleet not found."));
    }

    private List<Map<String, Object>> membershipRows(long fleetId, boolean leadersOnly) {
        String filter = leadersOnly ? " and r.is_leadership=true and m.status='active'" : "";
        return jdbc.query(MEMBERSHIP_SELECT + " where m.fleet_id=:fleetId" + filter + """
                order by case when m.status='pending' then 0 when m.status='active' then 1 else 2 end,
                         r.rank desc, lower(coalesce(up.display_name,u.username)), m.id
                """, Map.of("fleetId", fleetId));
    }

    private FleetRead fleetRead(Map<String, Object> row) {
        long id = RowValues.longValue(row, "id");
        List<FleetMembershipRead> leaders = membershipRows(id, true).stream()
                .map(item -> membership(item, null)).toList();
        return new FleetRead(
                RowValues.nullableLong(row, "active_count"), RowValues.dateTime(row, "created_at"),
                RowValues.string(row, "description"), RowValues.requiredString(row, "focus"), id,
                RowValues.booleanValue(row, "is_active"), leaders, RowValues.requiredString(row, "name"),
                RowValues.nullableLong(row, "pending_count"), RowValues.requiredString(row, "slug"),
                RowValues.longValue(row, "sort_order"), RowValues.string(row, "standing_orders"),
                RowValues.dateTime(row, "updated_at"));
    }

    private FleetMembershipRead membership(Map<String, Object> row, AuthenticatedUser actor) {
        FleetMemberUserRead user = new FleetMemberUserRead(
                RowValues.requiredString(row, "display_name"), RowValues.longValue(row, "user_id"),
                RowValues.requiredString(row, "site_role"), RowValues.requiredString(row, "username"));
        return new FleetMembershipRead(
                RowValues.string(row, "admin_note"), RowValues.string(row, "assignment"),
                RowValues.string(row, "availability"), RowValues.string(row, "discord_handle"),
                RowValues.longValue(row, "fleet_id"), RowValues.longValue(row, "id"),
                RowValues.dateTime(row, "joined_at"), actor == null ? null : policy.permissions(actor,
                        RowValues.longValue(row, "fleet_id"), row),
                RowValues.string(row, "note"), RowValues.string(row, "preferred_roles"),
                RowValues.string(row, "preferred_ships"), RowValues.requiredString(row, "role"),
                RowValues.requiredString(row, "status"), RowValues.string(row, "timezone"),
                RowValues.dateTime(row, "updated_at"), user, RowValues.longValue(row, "user_id"));
    }

    private FleetMembershipSelfRead selfMembership(Map<String, Object> row) {
        FleetMembershipRead member = membership(row, null);
        FleetMembershipFleetRead fleet = new FleetMembershipFleetRead(
                RowValues.requiredString(row, "fleet_focus"), RowValues.longValue(row, "fleet_id"),
                RowValues.booleanValue(row, "fleet_active"), RowValues.requiredString(row, "fleet_name"),
                RowValues.requiredString(row, "fleet_slug"));
        return new FleetMembershipSelfRead(
                member.adminNote(), member.assignment(), member.availability(), member.discordHandle(), fleet,
                member.fleetId(), member.id(), member.joinedAt(), member.management(), member.note(),
                member.preferredRoles(), member.preferredShips(), member.role(), member.status(), member.timezone(),
                member.updatedAt(), member.user(), member.userId());
    }
}
