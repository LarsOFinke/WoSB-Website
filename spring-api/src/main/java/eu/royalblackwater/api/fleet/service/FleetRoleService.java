package eu.royalblackwater.api.fleet.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.FleetRoleCreate;
import eu.royalblackwater.api.dto.FleetRoleRead;
import eu.royalblackwater.api.dto.FleetRoleUpdate;
import eu.royalblackwater.api.fleet.mapper.FleetDtoMapper;
import eu.royalblackwater.api.fleet.repository.FleetDataRepository;
import eu.royalblackwater.api.fleet.repository.queries.FleetRoleQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
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
    private final FleetDataRepository repository;
    private final FleetAccessPolicy policy;
    private final AuditService audit;
    private final Clock clock;
    private final FleetDtoMapper mapper;

    public FleetRoleService(FleetDataRepository repository, FleetAccessPolicy policy, AuditService audit, Clock clock, FleetDtoMapper mapper) {
        this.repository = repository;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public List<FleetRoleRead> list(long fleetId, boolean includeInactive, AuthenticatedUser actor) {
        requireFleet(fleetId);
        policy.requireFleetManager(actor, fleetId);
        String filter = includeInactive ? "" : FleetRoleQueries.LIST_WHERE_01;
        return repository.query(FleetRoleQueries.SELECT + filter + FleetRoleQueries.LIST_ORDER_BY_01, Map.of()).stream()
                .map(mapper::role).toList();
    }

    @Transactional
    public FleetRoleRead create(long fleetId, FleetRoleCreate payload, AuthenticatedUser actor) {
        requireFleet(fleetId);
        policy.requireRoleManager(actor, fleetId);
        String code = normalizeCode(payload.code());
        if (repository.count(FleetRoleQueries.CREATE_SELECT_01, Map.of("code", code)) > 0) {
            throw bad("A fleet role with this code already exists.");
        }
        boolean manageFleet = Boolean.TRUE.equals(payload.canManageFleet());
        boolean manageMembers = Boolean.TRUE.equals(payload.canManageMembers());
        boolean leadership = Boolean.TRUE.equals(payload.isLeadership()) || manageFleet || manageMembers;
        LocalDateTime now = now();
        long id = repository.insertReturningId(FleetRoleQueries.CREATE_INSERT_01, Map.of(
                        "code", code, "label", payload.label().strip(), "rank", payload.rank(),
                        "leadership", leadership, "manageFleet", manageFleet,
                        "manageMembers", manageMembers, "now", now));
        audit.record(actor, "fleet_role", id, "create", "Fleet role “" + payload.label().strip() + "” created.",
                List.of("code", "label", "rank", "is_leadership", "can_manage_fleet", "can_manage_members"),
                "fleet", fleetId);
        return find(id);
    }

    @Transactional
    public FleetRoleRead update(long fleetId, long roleId, FleetRoleUpdate payload, AuthenticatedUser actor) {
        requireFleet(fleetId);
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
            repository.update(update.sql(), update.parameters());
            audit.record(actor, "fleet_role", roleId, "update", "Fleet role #" + roleId + " updated.",
                    update.columns(), "fleet", fleetId);
        }
        return find(roleId);
    }

    @Transactional
    public void delete(long fleetId, long roleId, AuthenticatedUser actor) {
        requireFleet(fleetId);
        policy.requireRoleManager(actor, fleetId);
        Map<String, Object> existing = raw(roleId);
        if (RowValues.booleanValue(existing, "is_system")) {
            throw bad("System fleet roles cannot be deleted.");
        }
        if (RowValues.longValue(existing, "member_count") > 0) {
            throw bad("Reassign all members before deleting this fleet role.");
        }
        repository.update(FleetRoleQueries.DELETE_DELETE_01, Map.of("id", roleId));
        audit.record(actor, "fleet_role", roleId, "delete", "Fleet role #" + roleId + " deleted.",
                List.of(), "fleet", fleetId);
    }

    private void requireFleet(long fleetId) {
        if (repository.count(FleetRoleQueries.FLEET_EXISTS_SELECT_01, Map.of("id", fleetId)) == 0) {
            throw new ResponseStatusException(NOT_FOUND, "Fleet not found.");
        }
    }

    private FleetRoleRead find(long roleId) {
        return mapper.role(raw(roleId));
    }

    private Map<String, Object> raw(long roleId) {
        return repository.optional(FleetRoleQueries.SELECT + FleetRoleQueries.RAW_WHERE_01, Map.of("id", roleId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Fleet role not found."));
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
