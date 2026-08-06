package eu.royalblackwater.api.squads.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.SquadCreate;
import eu.royalblackwater.api.dto.SquadDetailRead;
import eu.royalblackwater.api.dto.SquadMemberCreate;
import eu.royalblackwater.api.dto.SquadMemberRead;
import eu.royalblackwater.api.dto.SquadMemberUpdate;
import eu.royalblackwater.api.dto.SquadRosterMemberRead;
import eu.royalblackwater.api.dto.SquadSummaryRead;
import eu.royalblackwater.api.dto.SquadUpdate;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.persistence.SqlUpdate;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.squads.filter.SquadListFilter;
import eu.royalblackwater.api.squads.mapper.SquadDtoMapper;
import eu.royalblackwater.api.squads.repository.SquadRepository;
import eu.royalblackwater.api.squads.repository.queries.SquadQueries;
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
    private final SquadRepository repository;
    private final FleetAccessPolicy fleetPolicy;
    private final SquadAccessPolicy policy;
    private final AuditService audit;
    private final Clock clock;
    public SquadService(SquadRepository repository, FleetAccessPolicy fleetPolicy, SquadAccessPolicy policy,
                        AuditService audit, Clock clock) {
        this.repository = repository;
        this.fleetPolicy = fleetPolicy;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
    }
    @Transactional(readOnly = true)
    public List<SquadSummaryRead> list(AuthenticatedUser actor, SquadListFilter filter) {
        StringBuilder sql = new StringBuilder(SquadQueries.SQUAD_SELECT + SquadQueries.LIST_WHERE_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (!filter.includeInactive()) {
            sql.append(SquadQueries.LIST_AND_01);
        } else if (!actor.staff()) {
            sql.append(SquadQueries.LIST_AND_02);
            parameters.put("accessUserId", actor.id());
        }
        if (filter.mineOnly()) {
            sql.append(SquadQueries.LIST_AND_03)
                    .append(SquadQueries.LIST_ON_01)
                    .append(SquadQueries.LIST_AND_04);
            parameters.put("userId", actor.id());
        }
        if (filter.page().search() != null) {
            sql.append(SquadQueries.LIST_AND_05)
                    .append(SquadQueries.LIST_OR_01);
            parameters.put("search", "%" + filter.page().search().toLowerCase(Locale.ROOT) + "%");
        }
        if (filter.fleetId() != null) {
            sql.append(SquadQueries.LIST_AND_06);
            parameters.put("fleetId", filter.fleetId());
        }
        sql.append(SquadQueries.LIST_ORDER_BY_01);
        parameters.put("limit", filter.page().limit());
        parameters.put("offset", filter.page().offset());
        List<Map<String, Object>> squads = repository.query(sql.toString(), parameters);
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
        return repository.query(SquadQueries.ROSTER_SELECT_01, Map.of("fleetId", fleetId)).stream()
                .map(row -> SquadDtoMapper.roster(row, arrayLongs(row.get("squad_ids")))).toList();
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
        long id = repository.insertReturningId(SquadQueries.CREATE_INSERT_01, SqlParameters.ofNullable(
                        "fleetId", fleetId, "name", name, "slug", slug,
                        "description", blank(payload.description()), "focus", blank(payload.focus()),
                        "maxMembers", payload.maxMembers(), "actorId", actor.id(), "now", now));
        long leaderRoleId = roleId("leader");
        repository.insertReturningId(SquadQueries.CREATE_INSERT_02, Map.of("squadId", id, "membershipId", RowValues.longValue(leader, "id"),
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
            update.set("updated_at", now()); repository.update(update.sql(), update.parameters());
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
        repository.update(SquadQueries.ARCHIVE_UPDATE_01,
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
        Map<String, Object> existing = repository.optional(SquadQueries.ADD_MEMBER_SELECT_01, Map.of("squadId", squadId, "membershipId", payload.fleetMembershipId())).orElse(null);
        long memberId;
        if (existing == null) {
            validateMaximum(RowValues.nullableLong(squad, "max_members"), RowValues.longValue(squad, "member_count") + 1);
            memberId = repository.insertReturningId(SquadQueries.ADD_MEMBER_INSERT_01, SqlParameters.ofNullable(
                            "squadId", squadId, "membershipId", RowValues.longValue(membership, "id"),
                            "roleId", roleId(role), "note", blank(payload.note()), "now", now()));
        } else {
            memberId = RowValues.longValue(existing, "id");
            repository.update(SquadQueries.ADD_MEMBER_UPDATE_01, SqlParameters.ofNullable("roleId", roleId(role), "note", blank(payload.note()),
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
            update.set("updated_at", now()); repository.update(update.sql(), update.parameters());
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
        repository.update(SquadQueries.REMOVE_MEMBER_DELETE_01, Map.of("id", memberId));
        audit.record(actor, "squad_member", memberId, "delete", "Squad member removed.", List.of());
        return get(squadId, actor);
    }
    private SquadDetailRead detail(Map<String, Object> squad, AuthenticatedUser actor) {
        long squadId = RowValues.longValue(squad, "id");
        long fleetId = RowValues.longValue(squad, "fleet_id");
        List<Map<String, Object>> rawMembers = memberRows(List.of(squadId)).getOrDefault(squadId, List.of());
        SquadSummaryRead summary = summary(squad, actor, rawMembers, fleetPolicy.canManageFleet(actor, fleetId));
        List<SquadMemberRead> members = rawMembers.stream().map(row -> member(row, summary.canManage())).toList();
        return SquadDtoMapper.detail(summary, members);
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
        return SquadDtoMapper.summary(squad, currentRole, currentRow != null, manage, administer, leader, members.size());
    }
    private Map<Long, List<Map<String, Object>>> memberRows(List<Long> squadIds) {
        Map<Long, List<Map<String, Object>>> result = new LinkedHashMap<>();
        if (squadIds.isEmpty()) return result;
        for (Map<String, Object> row : repository.query(SquadQueries.MEMBER_SELECT + SquadQueries.MEMBER_ROWS_WHERE_01, Map.of("ids", squadIds))) {
            result.computeIfAbsent(RowValues.longValue(row, "squad_id"), ignored -> new ArrayList<>()).add(row);
        }
        return result;
    }
    private static SquadMemberRead member(Map<String, Object> row, boolean includeNote) {
        return SquadDtoMapper.member(row, includeNote);
    }
    private Map<String, Object> raw(long id) {
        return repository.optional(SquadQueries.SQUAD_SELECT + SquadQueries.RAW_WHERE_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Squad not found."));
    }
    private Map<String, Object> memberRaw(long squadId, long memberId) {
        return repository.optional(SquadQueries.MEMBER_SELECT + SquadQueries.MEMBER_RAW_WHERE_01,
                Map.of("squadId", squadId, "memberId", memberId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Squad member not found."));
    }
    private Map<String, Object> officialFleet() {
        return repository.optional(SquadQueries.OFFICIAL_FLEET_SELECT_01, Map.of()).orElseThrow(() -> bad("Official fleet not found."));
    }
    private Map<String, Object> activeMembership(long fleetId, long membershipId) {
        return repository.optional(SquadQueries.ACTIVE_MEMBERSHIP_SELECT_01, Map.of("id", membershipId, "fleetId", fleetId))
                .orElseThrow(() -> bad("The selected player is not an active member of this fleet."));
    }
    private long roleId(String role) {
        return repository.optional(SquadQueries.ROLE_ID_SELECT_01, Map.of("code", role))
                .map(row -> RowValues.longValue(row, "id")).orElseThrow(() -> bad("Invalid squad role."));
    }
    private void transferLeadership(long squadId, long memberId) {
        long leader = roleId("leader"), officer = roleId("officer");
        repository.update(SquadQueries.TRANSFER_LEADERSHIP_UPDATE_01, Map.of("memberId", memberId, "leader", leader, "officer", officer,
                        "now", now(), "squadId", squadId));
    }
    private void ensureUniqueName(long fleetId, String name, Long excluded) {
        String exclusion = excluded == null ? "" : SquadQueries.ENSURE_UNIQUE_NAME_AND_01;
        long count = repository.count(SquadQueries.ENSURE_UNIQUE_NAME_SELECT_01 + exclusion, SqlParameters.ofNullable("fleetId", fleetId, "name", name, "excluded", excluded));
        if (count > 0) throw bad("A squad with this name already exists.");
    }
    private String uniqueSlug(long fleetId, String name, Long excluded) {
        String base = slugify(name), candidate = base;
        String exclusion = excluded == null ? "" : SquadQueries.ENSURE_UNIQUE_NAME_AND_01;
        for (int suffix = 2; suffix < 10000; suffix++) {
            long count = repository.count(SquadQueries.UNIQUE_SLUG_SELECT_01 + exclusion,
                    SqlParameters.ofNullable("fleetId", fleetId, "slug", candidate, "excluded", excluded));
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
