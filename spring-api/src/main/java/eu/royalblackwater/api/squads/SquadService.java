package eu.royalblackwater.api.squads;
import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.SquadCreate;
import eu.royalblackwater.api.contract.SquadDetailRead;
import eu.royalblackwater.api.contract.SquadMemberCreate;
import eu.royalblackwater.api.contract.SquadMemberRead;
import eu.royalblackwater.api.contract.SquadMemberUpdate;
import eu.royalblackwater.api.contract.SquadRosterMemberRead;
import eu.royalblackwater.api.contract.SquadSummaryRead;
import eu.royalblackwater.api.contract.SquadUpdate;
import eu.royalblackwater.api.fleet.FleetAccessPolicy;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.persistence.SqlUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.text.Normalizer;
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
public class SquadService {
    private static final Set<String> ROLES = Set.of("member", "officer", "leader");
    private static final String SQUAD_SELECT = """
            select s.*, (select count(*) from squad_members sm where sm.squad_id=s.id) member_count
            from squads s
            """;
    private static final String MEMBER_SELECT = """
            select sm.*, sr.code as squad_role, fr.code as fleet_role, fm.user_id,
                   coalesce(up.display_name,u.username) as display_name
            from squad_members sm join squad_roles sr on sr.id=sm.squad_role_id
            join fleet_memberships fm on fm.id=sm.fleet_membership_id
            join fleet_roles fr on fr.id=fm.fleet_role_id
            join users u on u.id=fm.user_id left join user_profiles up on up.user_id=u.id
            """;
    private final JdbcQueryService jdbc;
    private final FleetAccessPolicy fleetPolicy;
    private final SquadAccessPolicy policy;
    private final AuditService audit;
    private final Clock clock;
    public SquadService(JdbcQueryService jdbc, FleetAccessPolicy fleetPolicy, SquadAccessPolicy policy,
                        AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.fleetPolicy = fleetPolicy;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
    }
    @Transactional(readOnly = true)
    public List<SquadSummaryRead> list(AuthenticatedUser actor, SquadListFilter filter) {
        StringBuilder sql = new StringBuilder(SQUAD_SELECT + " where 1=1");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (!filter.includeInactive()) {
            sql.append(" and s.is_active=true");
        } else if (!actor.staff()) {
            sql.append("""
                     and (s.is_active=true or exists(
                         select 1 from fleet_memberships fm join fleet_roles fr on fr.id=fm.fleet_role_id
                         where fm.fleet_id=s.fleet_id and fm.user_id=:accessUserId and fm.status='active'
                           and fr.can_manage_fleet=true and fr.is_active=true))
                    """);
            parameters.put("accessUserId", actor.id());
        }
        if (filter.mineOnly()) {
            sql.append(" and exists(select 1 from squad_members sm join fleet_memberships fm")
                    .append(" on fm.id=sm.fleet_membership_id where sm.squad_id=s.id")
                    .append(" and fm.user_id=:userId and fm.status='active')");
            parameters.put("userId", actor.id());
        }
        if (filter.page().search() != null) {
            sql.append(" and (lower(s.name) like :search or lower(coalesce(s.description,'')) like :search")
                    .append(" or lower(coalesce(s.focus,'')) like :search)");
            parameters.put("search", "%" + filter.page().search().toLowerCase(Locale.ROOT) + "%");
        }
        if (filter.fleetId() != null) {
            sql.append(" and s.fleet_id=:fleetId");
            parameters.put("fleetId", filter.fleetId());
        }
        sql.append(" order by s.name,s.id limit :limit offset :offset");
        parameters.put("limit", filter.page().limit());
        parameters.put("offset", filter.page().offset());
        List<Map<String, Object>> squads = jdbc.query(sql.toString(), parameters);
        if (squads.isEmpty()) return List.of();
        List<Long> squadIds = squads.stream().map(row -> RowValues.longValue(row, "id")).toList();
        List<Long> fleetIds = squads.stream().map(row -> RowValues.longValue(row, "fleet_id")).distinct().toList();
        Set<Long> managedFleetIds = fleetPolicy.managedFleetIds(actor, fleetIds);
        Map<Long, List<Map<String, Object>>> members = memberRows(squadIds);
        return squads.stream().map(row -> summary(row, actor,
                members.getOrDefault(RowValues.longValue(row, "id"), List.of()),
                managedFleetIds.contains(RowValues.longValue(row, "fleet_id")))).toList();
    }
    @Transactional(readOnly = true)
    public SquadDetailRead get(long squadId, AuthenticatedUser actor) {
        Map<String, Object> squad = raw(squadId);
        long fleetId = RowValues.longValue(squad, "fleet_id");
        if (!RowValues.booleanValue(squad, "is_active") && !policy.canManage(actor, squadId, fleetId)) {
            throw new ResponseStatusException(NOT_FOUND, "Squad not found.");
        }
        return detail(squad, actor);
    }
    @Transactional(readOnly = true)
    public List<SquadRosterMemberRead> roster(AuthenticatedUser actor) {
        Map<String, Object> fleet = officialFleet();
        long fleetId = RowValues.longValue(fleet, "id");
        if (!fleetPolicy.canManageFleet(actor, fleetId) && !policy.hasManagedSquad(actor)) {
            throw new ResponseStatusException(FORBIDDEN, "Squad leadership access required.");
        }
        return jdbc.query("""
                select fm.id fleet_membership_id,fm.user_id,fr.code fleet_role,
                       coalesce(up.display_name,u.username) display_name,
                       coalesce(array_agg(sm.squad_id order by sm.squad_id)
                           filter(where s.is_active=true),array[]::integer[]) squad_ids
                from fleet_memberships fm join users u on u.id=fm.user_id
                join fleet_roles fr on fr.id=fm.fleet_role_id
                left join user_profiles up on up.user_id=u.id
                left join squad_members sm on sm.fleet_membership_id=fm.id
                left join squads s on s.id=sm.squad_id
                where fm.fleet_id=:fleetId and fm.status='active'
                group by fm.id,fm.user_id,fr.code,up.display_name,u.username
                order by lower(coalesce(up.display_name,u.username))
                """, Map.of("fleetId", fleetId)).stream().map(row -> new SquadRosterMemberRead(
                        RowValues.requiredString(row, "display_name"), RowValues.longValue(row, "fleet_membership_id"),
                        RowValues.requiredString(row, "fleet_role"), arrayLongs(row.get("squad_ids")),
                        RowValues.longValue(row, "user_id"))).toList();
    }
    @Transactional
    public SquadDetailRead create(SquadCreate payload, AuthenticatedUser actor) {
        Map<String, Object> fleet = officialFleet();
        long fleetId = RowValues.longValue(fleet, "id");
        if (!fleetPolicy.canManageFleet(actor, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN, "Fleet leadership access required to create squads.");
        }
        String name = required(payload.name());
        ensureUniqueName(fleetId, name, null);
        Map<String, Object> leader = activeMembership(fleetId, payload.leaderMembershipId());
        String slug = uniqueSlug(fleetId, name, null);
        validateMaximum(payload.maxMembers(), 0);
        LocalDateTime now = now();
        long id = jdbc.insertReturningId("""
                insert into squads(fleet_id,name,slug,description,focus,max_members,is_active,created_by_id,created_at,updated_at)
                values(:fleetId,:name,:slug,:description,:focus,:maxMembers,true,:actorId,:now,:now) returning id
                """, SqlParameters.ofNullable(
                        "fleetId", fleetId, "name", name, "slug", slug,
                        "description", blank(payload.description()), "focus", blank(payload.focus()),
                        "maxMembers", payload.maxMembers(), "actorId", actor.id(), "now", now));
        long leaderRoleId = roleId("leader");
        jdbc.insertReturningId("""
                insert into squad_members(squad_id,fleet_membership_id,squad_role_id,joined_at,updated_at)
                values(:squadId,:membershipId,:roleId,:now,:now) returning id
                """, Map.of("squadId", id, "membershipId", RowValues.longValue(leader, "id"),
                        "roleId", leaderRoleId, "now", now));
        audit.record(actor, "squad", id, "create", "Squad “" + name + "” created.",
                List.of("name", "leader", "focus", "max_members"));
        return get(id, actor);
    }
    @Transactional
    public SquadDetailRead update(long squadId, SquadUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> squad = raw(squadId);
        long fleetId = RowValues.longValue(squad, "fleet_id");
        policy.requireManage(actor, squadId, fleetId);
        long memberCount = RowValues.longValue(squad, "member_count");
        validateMaximum(payload.maxMembers(), memberCount);
        SqlUpdate update = new SqlUpdate("squads", "id", squadId);
        if (payload.name() != null) {
            String name = required(payload.name());
            ensureUniqueName(fleetId, name, squadId);
            update.set("name", name).set("slug", uniqueSlug(fleetId, name, squadId));
        }
        if (payload.description() != null) update.set("description", blank(payload.description()));
        if (payload.focus() != null) update.set("focus", blank(payload.focus()));
        if (payload.maxMembers() != null) update.set("max_members", payload.maxMembers());
        if (!update.isEmpty()) {
            update.set("updated_at", now()); jdbc.update(update.sql(), update.parameters());
            audit.record(actor, "squad", squadId, "update", "Squad #" + squadId + " updated.", update.columns());
        }
        return get(squadId, actor);
    }
    @Transactional
    public void archive(long squadId, AuthenticatedUser actor) {
        Map<String, Object> squad = raw(squadId);
        long fleetId = RowValues.longValue(squad, "fleet_id");
        if (!fleetPolicy.canManageFleet(actor, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN, "Fleet leadership access required to archive squads.");
        }
        jdbc.update("update squads set is_active=false,updated_at=:now where id=:id",
                Map.of("now", now(), "id", squadId));
        audit.record(actor, "squad", squadId, "archive", "Squad #" + squadId + " archived.", List.of("is_active"));
    }
    @Transactional
    public SquadDetailRead addMember(long squadId, SquadMemberCreate payload, AuthenticatedUser actor) {
        Map<String, Object> squad = raw(squadId);
        long fleetId = RowValues.longValue(squad, "fleet_id");
        if (!RowValues.booleanValue(squad, "is_active")) throw new ResponseStatusException(NOT_FOUND, "Squad not found.");
        policy.requireManage(actor, squadId, fleetId);
        String role = normalizeRole(payload.role() == null ? "member" : payload.role());
        if (!"member".equals(role)) policy.requireAdminister(actor, squadId, fleetId);
        Map<String, Object> membership = activeMembership(fleetId, payload.fleetMembershipId());
        Map<String, Object> existing = jdbc.optional("""
                select id from squad_members where squad_id=:squadId and fleet_membership_id=:membershipId
                """, Map.of("squadId", squadId, "membershipId", payload.fleetMembershipId())).orElse(null);
        long memberId;
        if (existing == null) {
            validateMaximum(RowValues.nullableLong(squad, "max_members"), RowValues.longValue(squad, "member_count") + 1);
            memberId = jdbc.insertReturningId("""
                    insert into squad_members(squad_id,fleet_membership_id,squad_role_id,note,joined_at,updated_at)
                    values(:squadId,:membershipId,:roleId,:note,:now,:now) returning id
                    """, SqlParameters.ofNullable(
                            "squadId", squadId, "membershipId", RowValues.longValue(membership, "id"),
                            "roleId", roleId(role), "note", blank(payload.note()), "now", now()));
        } else {
            memberId = RowValues.longValue(existing, "id");
            jdbc.update("""
                    update squad_members set squad_role_id=:roleId,note=:note,updated_at=:now where id=:id
                    """, SqlParameters.ofNullable("roleId", roleId(role), "note", blank(payload.note()),
                            "now", now(), "id", memberId));
        }
        if ("leader".equals(role)) transferLeadership(squadId, memberId);
        audit.record(actor, "squad_member", memberId, "upsert", "Squad member updated.", List.of("role", "note"));
        return get(squadId, actor);
    }
    @Transactional
    public SquadDetailRead updateMember(long squadId, long memberId, SquadMemberUpdate payload,
                                        AuthenticatedUser actor) {
        Map<String, Object> squad = raw(squadId);
        long fleetId = RowValues.longValue(squad, "fleet_id");
        policy.requireManage(actor, squadId, fleetId);
        Map<String, Object> member = memberRaw(squadId, memberId);
        SqlUpdate update = new SqlUpdate("squad_members", "id", memberId);
        if (payload.role() != null) {
            String requested = normalizeRole(payload.role());
            String current = RowValues.requiredString(member, "squad_role");
            if (!requested.equals(current)) policy.requireAdminister(actor, squadId, fleetId);
            if ("leader".equals(requested)) transferLeadership(squadId, memberId);
            else if ("leader".equals(current)) throw bad("Transfer squad leadership before demoting the current leader.");
            else update.set("squad_role_id", roleId(requested));
        }
        if (payload.note() != null) update.set("note", blank(payload.note()));
        if (!update.isEmpty()) {
            update.set("updated_at", now()); jdbc.update(update.sql(), update.parameters());
            audit.record(actor, "squad_member", memberId, "update", "Squad member updated.", update.columns());
        }
        return get(squadId, actor);
    }
    @Transactional
    public SquadDetailRead removeMember(long squadId, long memberId, AuthenticatedUser actor) {
        Map<String, Object> squad = raw(squadId);
        long fleetId = RowValues.longValue(squad, "fleet_id");
        policy.requireManage(actor, squadId, fleetId);
        Map<String, Object> member = memberRaw(squadId, memberId);
        String role = RowValues.requiredString(member, "squad_role");
        if ("leader".equals(role)) throw bad("Transfer squad leadership before removing the current leader.");
        if ("officer".equals(role)) policy.requireAdminister(actor, squadId, fleetId);
        jdbc.update("delete from squad_members where id=:id", Map.of("id", memberId));
        audit.record(actor, "squad_member", memberId, "delete", "Squad member removed.", List.of());
        return get(squadId, actor);
    }
    private SquadDetailRead detail(Map<String, Object> squad, AuthenticatedUser actor) {
        long squadId = RowValues.longValue(squad, "id");
        long fleetId = RowValues.longValue(squad, "fleet_id");
        List<Map<String, Object>> rawMembers = memberRows(List.of(squadId)).getOrDefault(squadId, List.of());
        SquadSummaryRead summary = summary(squad, actor, rawMembers, fleetPolicy.canManageFleet(actor, fleetId));
        List<SquadMemberRead> members = rawMembers.stream().map(row -> member(row, summary.canManage())).toList();
        return new SquadDetailRead(summary.canAdminister(), summary.canManage(), summary.createdAt(),
                summary.currentUserRole(), summary.description(), summary.fleetId(), summary.focus(), summary.id(),
                summary.isActive(), summary.isMember(), summary.leader(), summary.maxMembers(), summary.memberCount(),
                members, summary.name(), summary.slug(), summary.updatedAt());
    }
    private SquadSummaryRead summary(Map<String, Object> squad, AuthenticatedUser actor,
                                     List<Map<String, Object>> rawMembers, boolean managesFleet) {
        long id = RowValues.longValue(squad, "id");
        long fleetId = RowValues.longValue(squad, "fleet_id");
        Map<String, Object> currentRow = rawMembers.stream()
                .filter(row -> RowValues.longValue(row, "user_id") == actor.id()).findFirst().orElse(null);
        String currentRole = currentRow == null ? null : RowValues.requiredString(currentRow, "squad_role");
        boolean manage = managesFleet || "leader".equals(currentRole) || "officer".equals(currentRole);
        boolean administer = managesFleet || "leader".equals(currentRole);
        List<SquadMemberRead> members = rawMembers.stream().map(row -> member(row, manage)).toList();
        SquadMemberRead leader = members.stream().filter(m -> "leader".equals(m.squadRole())).findFirst().orElse(null);
        return new SquadSummaryRead(administer, manage, RowValues.dateTime(squad, "created_at"),
                currentRole, RowValues.string(squad, "description"), fleetId,
                RowValues.string(squad, "focus"), id, RowValues.booleanValue(squad, "is_active"), currentRow != null,
                leader, RowValues.nullableLong(squad, "max_members"), members.size(),
                RowValues.requiredString(squad, "name"), RowValues.requiredString(squad, "slug"),
                RowValues.dateTime(squad, "updated_at"));
    }
    private Map<Long, List<Map<String, Object>>> memberRows(List<Long> squadIds) {
        Map<Long, List<Map<String, Object>>> result = new LinkedHashMap<>();
        if (squadIds.isEmpty()) return result;
        for (Map<String, Object> row : jdbc.query(MEMBER_SELECT + """
                where sm.squad_id in (:ids)
                order by sm.squad_id,sr.rank desc,lower(coalesce(up.display_name,u.username))
                """, Map.of("ids", squadIds))) {
            result.computeIfAbsent(RowValues.longValue(row, "squad_id"), ignored -> new ArrayList<>()).add(row);
        }
        return result;
    }
    private static SquadMemberRead member(Map<String, Object> row, boolean includeNote) {
        return new SquadMemberRead(RowValues.requiredString(row, "display_name"),
                RowValues.longValue(row, "fleet_membership_id"), RowValues.requiredString(row, "fleet_role"),
                RowValues.longValue(row, "id"), RowValues.dateTime(row, "joined_at"),
                includeNote ? RowValues.string(row, "note") : null, RowValues.requiredString(row, "squad_role"),
                RowValues.longValue(row, "user_id"));
    }
    private Map<String, Object> raw(long id) {
        return jdbc.optional(SQUAD_SELECT + " where s.id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Squad not found."));
    }
    private Map<String, Object> memberRaw(long squadId, long memberId) {
        return jdbc.optional(MEMBER_SELECT + " where sm.squad_id=:squadId and sm.id=:memberId",
                Map.of("squadId", squadId, "memberId", memberId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Squad member not found."));
    }
    private Map<String, Object> officialFleet() {
        return jdbc.optional("""
                select * from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end,sort_order,id limit 1
                """, Map.of()).orElseThrow(() -> bad("Official fleet not found."));
    }
    private Map<String, Object> activeMembership(long fleetId, long membershipId) {
        return jdbc.optional("""
                select * from fleet_memberships where id=:id and fleet_id=:fleetId and status='active'
                """, Map.of("id", membershipId, "fleetId", fleetId))
                .orElseThrow(() -> bad("The selected player is not an active member of this fleet."));
    }
    private long roleId(String role) {
        return jdbc.optional("select id from squad_roles where code=:code", Map.of("code", role))
                .map(row -> RowValues.longValue(row, "id")).orElseThrow(() -> bad("Invalid squad role."));
    }
    private void transferLeadership(long squadId, long memberId) {
        long leader = roleId("leader"), officer = roleId("officer");
        jdbc.update("""
                update squad_members set squad_role_id=case when id=:memberId then :leader else :officer end,
                       updated_at=:now
                where squad_id=:squadId and (id=:memberId or squad_role_id=:leader)
                """, Map.of("memberId", memberId, "leader", leader, "officer", officer,
                        "now", now(), "squadId", squadId));
    }
    private void ensureUniqueName(long fleetId, String name, Long excluded) {
        long count = jdbc.count("""
                select count(*) from squads where fleet_id=:fleetId and lower(name)=lower(:name)
                  and (:excluded is null or id<>:excluded)
                """, SqlParameters.ofNullable("fleetId", fleetId, "name", name, "excluded", excluded));
        if (count > 0) throw bad("A squad with this name already exists.");
    }
    private String uniqueSlug(long fleetId, String name, Long excluded) {
        String base = slugify(name), candidate = base;
        for (int suffix = 2; suffix < 10000; suffix++) {
            long count = jdbc.count("""
                    select count(*) from squads where fleet_id=:fleetId and slug=:slug
                      and (:excluded is null or id<>:excluded)
                    """, SqlParameters.ofNullable("fleetId", fleetId, "slug", candidate, "excluded", excluded));
            if (count == 0) return candidate;
            candidate = base + "-" + suffix;
        }
        throw new IllegalStateException("Could not allocate a unique squad slug.");
    }
    private static String slugify(String value) {
        String normalized = Normalizer.normalize(value, Normalizer.Form.NFKD)
                .replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "-")
                .replaceAll("(^-|-$)", "");
        return normalized.isBlank() ? "squad" : normalized;
    }
    private static void validateMaximum(Long max, long memberCount) {
        if (max == null) return;
        if (max < 2 || max > 200) throw bad("Maximum squad size must be between 2 and 200.");
        if (max < memberCount) throw bad("Maximum squad size cannot be lower than the current member count.");
    }
    private static String normalizeRole(String value) {
        String role = value.strip().toLowerCase(Locale.ROOT);
        if (!ROLES.contains(role)) throw bad("Invalid squad role.");
        return role;
    }
    private static List<Long> arrayLongs(Object value) {
        try {
            if (value instanceof java.sql.Array array) value = array.getArray();
        } catch (java.sql.SQLException exception) {
            throw new IllegalStateException("Could not read squad roster aggregation.", exception);
        }
        if (value instanceof Object[] values) {
            List<Long> result = new ArrayList<>();
            for (Object item : values) if (item instanceof Number number) result.add(number.longValue());
            return List.copyOf(result);
        }
        return List.of();
    }
    private static String required(String value) { if (value == null || value.isBlank()) throw bad("Name is required."); return value.strip(); }
    private static String blank(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
