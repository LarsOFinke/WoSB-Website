package eu.royalblackwater.api.groups;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.GroupCreate;
import eu.royalblackwater.api.contract.GroupJoinRequest;
import eu.royalblackwater.api.contract.GroupMemberRead;
import eu.royalblackwater.api.contract.GroupRead;
import eu.royalblackwater.api.contract.ShipRead;
import eu.royalblackwater.api.contract.UserReferenceRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.ships.ShipQueryService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class GroupService {
    private static final Set<String> FOCUS = Set.of(
            "pve_farming", "pve_imp_hunting", "pve_general", "pvp_open_world",
            "pvp_arena", "pvp_general", "trading", "other");
    private static final String GROUP_SELECT = """
            select g.*, u.username as owner_username, coalesce(up.display_name,u.username) as owner_display_name,
                   (select count(*) from group_members m where m.group_id=g.id and m.is_active=true) active_count
            from groups g join users u on u.id=g.owner_id left join user_profiles up on up.user_id=u.id
            """;
    private final JdbcQueryService jdbc;
    private final ShipQueryService ships;
    private final AuditService audit;
    private final Clock clock;

    public GroupService(JdbcQueryService jdbc, ShipQueryService ships, AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.ships = ships;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<GroupRead> list(String search, String focus, Long minRate, Long maxRate, Integer ownerId) {
        validateRates(minRate, maxRate);
        StringBuilder sql = new StringBuilder(GROUP_SELECT + " where 1=1");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (ownerId == null) sql.append(" and g.status='open'");
        else { sql.append(" and g.owner_id=:ownerId"); parameters.put("ownerId", ownerId); }
        if (search != null && !search.isBlank()) {
            sql.append(" and lower(concat_ws(' ',g.title,g.focus,g.description,g.expectations,g.activity_plan,g.contact_note,g.fleet_restriction)) like :search");
            parameters.put("search", "%" + search.strip().toLowerCase(Locale.ROOT) + "%");
        }
        if (focus != null && !focus.isBlank()) {
            sql.append(" and g.focus=:focus"); parameters.put("focus", focus.strip().toLowerCase(Locale.ROOT));
        }
        if (minRate != null) {
            sql.append(" and coalesce(g.max_ship_rate,1)<=:minRate"); parameters.put("minRate", minRate);
        }
        if (maxRate != null) {
            sql.append(" and coalesce(g.min_ship_rate,7)>=:maxRate"); parameters.put("maxRate", maxRate);
        }
        sql.append(ownerId == null
                ? " order by g.status asc,g.expires_at asc,g.created_at desc"
                : " order by g.created_at desc,g.id desc");
        return jdbc.query(sql.toString(), parameters).stream().map(this::read).toList();
    }

    @Transactional(readOnly = true)
    public GroupRead get(long id) {
        return read(raw(id));
    }

    @Transactional
    public GroupRead create(GroupCreate payload, AuthenticatedUser actor) {
        String focus = payload.focus() == null ? "pve_general" : payload.focus().strip().toLowerCase(Locale.ROOT);
        if (!FOCUS.contains(focus)) throw bad("Invalid group focus.");
        long maxMembers = payload.maxMembers() == null ? 5 : payload.maxMembers();
        if (maxMembers < 2 || maxMembers > 50) throw bad("Group size must be between 2 and 50.");
        validateRates(payload.minShipRate(), payload.maxShipRate());
        if (payload.scheduledStartAt() != null && payload.scheduledEndAt() != null
                && !payload.scheduledEndAt().isAfter(payload.scheduledStartAt())) {
            throw bad("End time must be after start time.");
        }
        LocalDateTime now = now();
        long id = jdbc.insertReturningId("""
                insert into groups
                    (title, focus, description, expectations, activity_plan, contact_note,
                     scheduled_start_at, scheduled_end_at, max_members, min_ship_rate, max_ship_rate,
                     allow_guests, fleet_restriction, status, owner_id, created_at, updated_at, expires_at)
                values (:title,:focus,:description,:expectations,:activityPlan,:contactNote,
                        :startAt,:endAt,:maxMembers,:minRate,:maxRate,:allowGuests,:fleetRestriction,
                        'open',:ownerId,:now,:now,:expiresAt) returning id
                """, SqlParameters.ofNullable(
                        "title", required(payload.title()), "focus", focus,
                        "description", blank(payload.description()), "expectations", blank(payload.expectations()),
                        "activityPlan", blank(payload.activityPlan()), "contactNote", blank(payload.contactNote()),
                        "startAt", payload.scheduledStartAt(), "endAt", payload.scheduledEndAt(),
                        "maxMembers", maxMembers, "minRate", payload.minShipRate(), "maxRate", payload.maxShipRate(),
                        "allowGuests", payload.allowGuests() == null || payload.allowGuests(),
                        "fleetRestriction", blank(payload.fleetRestriction()), "ownerId", actor.id(),
                        "now", now, "expiresAt", now.plusHours(24)));
        audit.record(actor, "group", id, "create", "Group “" + required(payload.title()) + "” created.",
                List.of("title", "focus", "max_members", "ship_rate", "schedule"));
        return get(id);
    }

    @Transactional
    public GroupRead join(long groupId, GroupJoinRequest payload, AuthenticatedUser actor) {
        Map<String, Object> group = raw(groupId);
        long active = RowValues.longValue(group, "active_count");
        long maximum = RowValues.longValue(group, "max_members");
        if (!"open".equals(group.get("status")) || !RowValues.dateTime(group, "expires_at").isAfter(now())) {
            throw bad("This group is not open for new members.");
        }
        if (active >= maximum) throw bad("This group is already full.");
        if (jdbc.count("""
                select count(*) from group_members where group_id=:groupId and user_id=:userId and is_active=true
                """, Map.of("groupId", groupId, "userId", actor.id())) > 0) {
            throw bad("You already joined this group.");
        }
        ResolvedSelection selection = resolveSelection(payload, actor);
        requireAllowedRate(group, selection.shipRate());
        String displayName = required(payload.displayName());
        if (displayName.equals(actor.username())) {
            displayName = jdbc.optional("""
                    select coalesce(p.display_name,u.username) display_name from users u
                    left join user_profiles p on p.user_id=u.id where u.id=:id
                    """, Map.of("id", actor.id())).map(row -> String.valueOf(row.get("display_name"))).orElse(displayName);
        }
        LocalDateTime now = now();
        jdbc.insertReturningId("""
                insert into group_members
                    (group_id,user_id,is_guest,display_name,fleet_name,ship_id,build_id,ship_name,
                     ship_rate,note,is_active,joined_at)
                values (:groupId,:userId,false,:displayName,:fleetName,:shipId,:buildId,:shipName,
                        :shipRate,:note,true,:now) returning id
                """, SqlParameters.ofNullable(
                        "groupId", groupId, "userId", actor.id(), "displayName", displayName,
                        "fleetName", blank(payload.fleetName()), "shipId", selection.shipId(),
                        "buildId", selection.buildId(), "shipName", selection.shipName(),
                        "shipRate", selection.shipRate(), "note", blank(payload.note()), "now", now));
        if (active + 1 >= maximum) {
            jdbc.update("update groups set status='full',updated_at=:now where id=:id",
                    Map.of("now", now, "id", groupId));
        }
        audit.record(actor, "group", groupId, "join", "Joined group #" + groupId + ".", List.of("members"));
        return get(groupId);
    }

    @Transactional
    public void close(long groupId, AuthenticatedUser actor) {
        Map<String, Object> group = raw(groupId);
        if (RowValues.longValue(group, "owner_id") != actor.id() && !actor.staff()) {
            throw new ResponseStatusException(FORBIDDEN, "You can only close your own groups.");
        }
        if (!"closed".equals(group.get("status"))) {
            LocalDateTime now = now();
            jdbc.update("update groups set status='closed',closed_at=:now,updated_at=:now where id=:id",
                    Map.of("now", now, "id", groupId));
            audit.record(actor, "group", groupId, "close", "Group #" + groupId + " closed.", List.of("status"));
        }
    }

    private GroupRead read(Map<String, Object> row) {
        long id = RowValues.longValue(row, "id");
        long active = RowValues.longValue(row, "active_count");
        long max = RowValues.longValue(row, "max_members");
        String storedStatus = RowValues.requiredString(row, "status");
        String status = "closed".equals(storedStatus) ? storedStatus : active >= max ? "full" : "open";
        List<GroupMemberRead> members = jdbc.query("""
                select * from group_members where group_id=:id order by joined_at,id
                """, Map.of("id", id)).stream().map(this::member).toList();
        boolean joinable = "open".equals(status) && active < max && RowValues.dateTime(row, "expires_at").isAfter(now());
        return new GroupRead(
                active, RowValues.string(row, "activity_plan"), RowValues.booleanValue(row, "allow_guests"),
                RowValues.nullableDateTime(row, "closed_at"), RowValues.string(row, "contact_note"),
                RowValues.dateTime(row, "created_at"), RowValues.string(row, "description"),
                RowValues.string(row, "expectations"), RowValues.dateTime(row, "expires_at"),
                RowValues.string(row, "fleet_restriction"), RowValues.string(row, "focus"), id, joinable, max,
                RowValues.nullableLong(row, "max_ship_rate"), members, RowValues.nullableLong(row, "min_ship_rate"),
                new UserReferenceRead(RowValues.requiredString(row, "owner_display_name"),
                        RowValues.longValue(row, "owner_id")), RowValues.longValue(row, "owner_id"),
                RowValues.nullableDateTime(row, "scheduled_end_at"),
                RowValues.nullableDateTime(row, "scheduled_start_at"), Math.max(0, max - active), status,
                RowValues.requiredString(row, "title"), RowValues.dateTime(row, "updated_at"));
    }

    private GroupMemberRead member(Map<String, Object> row) {
        Long shipId = RowValues.nullableLong(row, "ship_id");
        ShipRead ship = shipId == null ? null : ships.activeShip(shipId);
        return new GroupMemberRead(
                null, RowValues.nullableLong(row, "build_id"), RowValues.requiredString(row, "display_name"),
                RowValues.string(row, "fleet_name"), RowValues.longValue(row, "id"),
                RowValues.booleanValue(row, "is_active"), RowValues.booleanValue(row, "is_guest"),
                RowValues.dateTime(row, "joined_at"), RowValues.nullableDateTime(row, "left_at"),
                RowValues.string(row, "note"), ship, shipId, RowValues.string(row, "ship_name"),
                RowValues.nullableLong(row, "ship_rate"), RowValues.nullableLong(row, "user_id"));
    }

    private ResolvedSelection resolveSelection(GroupJoinRequest payload, AuthenticatedUser actor) {
        if (payload.buildId() != null) {
            Map<String, Object> row = jdbc.optional("""
                    select b.id build_id,b.ship_id,s.name ship_name,s.rate ship_rate
                    from builds b join ships s on s.id=b.ship_id
                    where b.id=:buildId and b.owner_id=:ownerId
                    """, Map.of("buildId", payload.buildId(), "ownerId", actor.id()))
                    .orElseThrow(() -> bad("The selected build does not belong to your account."));
            return new ResolvedSelection(RowValues.longValue(row, "build_id"),
                    RowValues.longValue(row, "ship_id"), RowValues.requiredString(row, "ship_name"),
                    RowValues.nullableLong(row, "ship_rate"));
        }
        if (payload.shipId() != null) {
            Map<String, Object> row = jdbc.optional("""
                    select id,name,rate from ships where id=:id and is_active=true
                    """, Map.of("id", payload.shipId()))
                    .orElseThrow(() -> bad("The selected ship does not exist."));
            return new ResolvedSelection(null, RowValues.longValue(row, "id"),
                    RowValues.requiredString(row, "name"), RowValues.nullableLong(row, "rate"));
        }
        return new ResolvedSelection(null, null, blank(payload.shipName()), payload.shipRate());
    }

    private static void validateRates(Long minRate, Long maxRate) {
        for (Long value : new Long[] {minRate, maxRate}) {
            if (value != null && (value < 1 || value > 7)) throw bad("Ship rate must be between 1 and 7.");
        }
        if (minRate != null && maxRate != null && maxRate > minRate) {
            throw bad("Maximum rate must be numerically lower than or equal to minimum rate.");
        }
    }

    private static void requireAllowedRate(Map<String, Object> group, Long rate) {
        Long min = RowValues.nullableLong(group, "min_ship_rate");
        Long max = RowValues.nullableLong(group, "max_ship_rate");
        if ((min != null || max != null) && rate == null) throw bad("This group requires a ship in the allowed range.");
        if (rate != null && ((min != null && rate > min) || (max != null && rate < max))) {
            throw bad("The selected ship is outside the allowed range.");
        }
    }

    private Map<String, Object> raw(long id) {
        return jdbc.optional(GROUP_SELECT + " where g.id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Group not found."));
    }

    private static String required(String value) {
        if (value == null || value.isBlank()) throw bad("A required text value is empty.");
        return value.strip();
    }

    private static String blank(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private record ResolvedSelection(Long buildId, Long shipId, String shipName, Long shipRate) { }
}
