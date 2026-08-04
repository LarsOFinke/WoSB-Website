package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.FleetRoleCreate;
import eu.royalblackwater.api.contract.FleetRoleRead;
import eu.royalblackwater.api.contract.FleetRoleUpdate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class FleetRoleService {
    private static final String SELECT = """
            select r.*, (select count(*) from fleet_memberships m where m.fleet_role_id=r.id) member_count
            from fleet_roles r
            """;
    private final JdbcQueryService jdbc;
    private final FleetAccessPolicy policy;
    private final AuditService audit;
    private final Clock clock;

    public FleetRoleService(JdbcQueryService jdbc, FleetAccessPolicy policy, AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<FleetRoleRead> list(boolean includeInactive) {
        String filter = includeInactive ? "" : " where r.is_active=true";
        return jdbc.query(SELECT + filter + " order by r.rank desc, r.label asc", Map.of()).stream()
                .map(FleetRoleService::read).toList();
    }

    @Transactional
    public FleetRoleRead create(long fleetId, FleetRoleCreate payload, AuthenticatedUser actor) {
        policy.requireRoleManager(actor, fleetId);
        String code = normalizeCode(payload.code());
        if (jdbc.count("select count(*) from fleet_roles where code=:code", Map.of("code", code)) > 0) {
            throw bad("A fleet role with this code already exists.");
        }
        boolean manageFleet = Boolean.TRUE.equals(payload.canManageFleet());
        boolean manageMembers = Boolean.TRUE.equals(payload.canManageMembers());
        boolean leadership = Boolean.TRUE.equals(payload.isLeadership()) || manageFleet || manageMembers;
        LocalDateTime now = now();
        long id = jdbc.insertReturningId("""
                insert into fleet_roles
                    (code, label, rank, is_leadership, can_manage_fleet, can_manage_members,
                     is_system, is_active, created_at, updated_at)
                values (:code, :label, :rank, :leadership, :manageFleet, :manageMembers,
                        false, true, :now, :now) returning id
                """, Map.of(
                        "code", code, "label", payload.label().strip(), "rank", payload.rank(),
                        "leadership", leadership, "manageFleet", manageFleet,
                        "manageMembers", manageMembers, "now", now));
        audit.record(actor, "fleet_role", id, "create", "Fleet role “" + payload.label().strip() + "” created.",
                List.of("code", "label", "rank", "is_leadership", "can_manage_fleet", "can_manage_members"));
        return find(id);
    }

    @Transactional
    public FleetRoleRead update(long fleetId, long roleId, FleetRoleUpdate payload, AuthenticatedUser actor) {
        policy.requireRoleManager(actor, fleetId);
        Map<String, Object> existing = raw(roleId);
        if (RowValues.booleanValue(existing, "is_system")) {
            throw bad("System fleet roles cannot be changed.");
        }
        if (Boolean.FALSE.equals(payload.isActive()) && RowValues.longValue(existing, "member_count") > 0) {
            throw bad("Reassign all members before deactivating this fleet role.");
        }
        SqlUpdate update = new SqlUpdate("fleet_roles", "id", roleId);
        if (payload.label() != null) update.set("label", payload.label().strip());
        if (payload.rank() != null) {
            if (payload.rank() < 1 || payload.rank() > 79) throw bad("Fleet role rank must be between 1 and 79.");
            update.set("rank", payload.rank());
        }
        if (payload.isLeadership() != null) update.set("is_leadership", payload.isLeadership());
        if (payload.canManageFleet() != null) update.set("can_manage_fleet", payload.canManageFleet());
        if (payload.canManageMembers() != null) update.set("can_manage_members", payload.canManageMembers());
        if (payload.isActive() != null) update.set("is_active", payload.isActive());
        boolean manageFleet = payload.canManageFleet() != null
                ? payload.canManageFleet() : RowValues.booleanValue(existing, "can_manage_fleet");
        boolean manageMembers = payload.canManageMembers() != null
                ? payload.canManageMembers() : RowValues.booleanValue(existing, "can_manage_members");
        if (manageFleet || manageMembers) update.set("is_leadership", true);
        if (!update.isEmpty()) {
            update.set("updated_at", now());
            jdbc.update(update.sql(), update.parameters());
            audit.record(actor, "fleet_role", roleId, "update", "Fleet role #" + roleId + " updated.",
                    update.columns());
        }
        return find(roleId);
    }

    @Transactional
    public void delete(long fleetId, long roleId, AuthenticatedUser actor) {
        policy.requireRoleManager(actor, fleetId);
        Map<String, Object> existing = raw(roleId);
        if (RowValues.booleanValue(existing, "is_system")) {
            throw bad("System fleet roles cannot be deleted.");
        }
        if (RowValues.longValue(existing, "member_count") > 0) {
            throw bad("Reassign all members before deleting this fleet role.");
        }
        jdbc.update("delete from fleet_roles where id=:id", Map.of("id", roleId));
        audit.record(actor, "fleet_role", roleId, "delete", "Fleet role #" + roleId + " deleted.", List.of());
    }

    private FleetRoleRead find(long roleId) {
        return read(raw(roleId));
    }

    private Map<String, Object> raw(long roleId) {
        return jdbc.optional(SELECT + " where r.id=:id", Map.of("id", roleId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Fleet role not found."));
    }

    private static FleetRoleRead read(Map<String, Object> row) {
        return new FleetRoleRead(
                RowValues.booleanValue(row, "can_manage_fleet"),
                RowValues.booleanValue(row, "can_manage_members"),
                RowValues.requiredString(row, "code"), RowValues.longValue(row, "id"),
                RowValues.booleanValue(row, "is_active"), RowValues.booleanValue(row, "is_leadership"),
                RowValues.booleanValue(row, "is_system"), RowValues.requiredString(row, "label"),
                RowValues.nullableLong(row, "member_count"), RowValues.longValue(row, "rank"));
    }

    private static String normalizeCode(String raw) {
        String code = raw.strip().toLowerCase(Locale.ROOT).replace('-', '_').replace(' ', '_');
        if (!code.matches("[a-z][a-z0-9_]{1,39}")) {
            throw bad("Role code must use lowercase letters, numbers and underscores.");
        }
        return code;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(BAD_REQUEST, message);
    }
}
