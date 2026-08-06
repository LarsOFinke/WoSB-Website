package eu.royalblackwater.api.fleet.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.FleetCreate;
import eu.royalblackwater.api.dto.FleetJoinRequest;
import eu.royalblackwater.api.dto.FleetMembershipRead;
import eu.royalblackwater.api.dto.FleetMembershipUpdate;
import eu.royalblackwater.api.dto.FleetRead;
import eu.royalblackwater.api.dto.FleetUpdate;
import eu.royalblackwater.api.fleet.dto.FleetMembershipTargetDto;
import eu.royalblackwater.api.fleet.mapper.FleetDtoMapper;
import eu.royalblackwater.api.fleet.repository.FleetDataRepository;
import eu.royalblackwater.api.fleet.repository.queries.FleetCommandQueries;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.persistence.SqlUpdate;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class FleetCommandService {
    private static final Set<String> FOCUS = Set.of(
            "trade", "faction", "port_battle", "training", "farming", "recon", "support", "mixed");
    private static final Set<String> STATUSES = Set.of("pending", "active", "inactive");
    private final FleetDataRepository repository;
    private final FleetViewService views;
    private final FleetAccessPolicy policy;
    private final AuditService audit;
    private final Clock clock;
    private final FleetDtoMapper mapper;

    public FleetCommandService(FleetDataRepository repository, FleetViewService views, FleetAccessPolicy policy,
                               AuditService audit, Clock clock, FleetDtoMapper mapper) {
        this.repository = repository;
        this.views = views;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional
    public FleetRead create(FleetCreate payload, AuthenticatedUser actor) {
        if (repository.count(FleetCommandQueries.CREATE_SELECT_01, Map.of()) > 0) {
            throw bad("The official fleet is already configured.");
        }
        String focus = focus(payload.focus());
        String name = payload.name().strip();
        String slug = slug(payload.slug());
        ensureUnique(name, slug, null);
        long id = repository.insertReturningId(FleetCommandQueries.CREATE_INSERT_01, SqlParameters.ofNullable(
                        "name", name, "slug", slug, "focus", focus,
                        "description", blank(payload.description()),
                        "standingOrders", blank(payload.standingOrders()),
                        "sortOrder", payload.sortOrder() == null ? 100 : payload.sortOrder(),
                        "active", payload.isActive() == null || payload.isActive(), "now", now()));
        audit.record(actor, "fleet", id, "create", "Fleet “" + name + "” created.",
                List.of("name", "slug", "focus", "description", "standing_orders", "sort_order", "is_active"));
        return views.read(id, true);
    }

    @Transactional
    public FleetRead update(long fleetId, FleetUpdate payload, AuthenticatedUser actor) {
        policy.requireFleetManager(actor, fleetId);
        Map<String, Object> existing = repository.optional(FleetCommandQueries.UPDATE_SELECT_01, Map.of("id", fleetId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Fleet not found."));
        String name = payload.name() == null ? String.valueOf(existing.get("name")) : payload.name().strip();
        String slug = payload.slug() == null ? String.valueOf(existing.get("slug")) : slug(payload.slug());
        ensureUnique(name, slug, fleetId);
        SqlUpdate update = new SqlUpdate("fleets", "id", fleetId);
        if (payload.name() != null) update.set("name", name);
        if (payload.slug() != null) update.set("slug", slug);
        if (payload.focus() != null) update.set("focus", focus(payload.focus()));
        if (payload.description() != null) update.set("description", blank(payload.description()));
        if (payload.standingOrders() != null) update.set("standing_orders", blank(payload.standingOrders()));
        if (payload.sortOrder() != null) update.set("sort_order", payload.sortOrder());
        if (payload.isActive() != null) update.set("is_active", payload.isActive());
        if (!update.isEmpty()) {
            update.set("updated_at", now());
            repository.update(update.sql(), update.parameters());
            audit.record(actor, "fleet", fleetId, "update", "Fleet “" + name + "” updated.", update.columns());
        }
        return views.read(fleetId, true);
    }

    @Transactional
    public FleetMembershipRead join(FleetJoinRequest payload, AuthenticatedUser actor) {
        Map<String, Object> fleet = official();
        long fleetId = ((Number) fleet.get("id")).longValue();
        if (payload.fleetId() != null && payload.fleetId() != fleetId) {
            throw bad("Only the official fleet can be joined.");
        }
        long roleId = roleId("member");
        Map<String, Object> existing = repository.optional(
                FleetCommandQueries.JOIN_SELECT_01, Map.of("userId", actor.id()))
                .orElse(null);
        long membershipId;
        if (existing == null) {
            membershipId = repository.insertReturningId(FleetCommandQueries.JOIN_INSERT_01, SqlParameters.ofNullable(
                            "fleetId", fleetId, "userId", actor.id(), "roleId", roleId,
                            "note", blank(payload.note()), "now", now()));
        } else {
            membershipId = ((Number) existing.get("id")).longValue();
            String status = "inactive".equals(existing.get("status")) ? "pending" : String.valueOf(existing.get("status"));
            repository.update(FleetCommandQueries.JOIN_UPDATE_01, SqlParameters.ofNullable(
                            "fleetId", fleetId, "status", status, "note", blank(payload.note()),
                            "now", now(), "id", membershipId));
        }
        return views.membership(membershipId, null);
    }

    @Transactional
    public FleetMembershipRead updateMembership(long fleetId, long membershipId,
                                                 FleetMembershipUpdate payload, AuthenticatedUser actor) {
        policy.requireFleetManager(actor, fleetId);
        FleetMembershipTargetDto target = targetMembership(fleetId, membershipId);
        FleetMembershipUpdate normalized = normalize(payload);
        policy.validateMembershipUpdate(actor, fleetId, target, normalized);
        SqlUpdate update = new SqlUpdate("fleet_memberships", "id", membershipId);
        if (normalized.role() != null) update.set("fleet_role_id", roleId(normalized.role()));
        if (normalized.status() != null) update.set("status", normalized.status());
        if (normalized.note() != null) update.set("note", blank(normalized.note()));
        if (normalized.assignment() != null) update.set("assignment", blank(normalized.assignment()));
        if (normalized.adminNote() != null) update.set("admin_note", blank(normalized.adminNote()));
        if (!update.isEmpty()) {
            update.set("updated_at", now());
            repository.update(update.sql(), update.parameters());
            audit.record(actor, "fleet_membership", membershipId, "update",
                    "Updated fleet membership for user #" + target.userId() + ".", update.columns());
        }
        return views.membership(membershipId, actor);
    }

    @Transactional
    public FleetMembershipRead assignLeader(long fleetId, long userId,
                                             FleetMembershipUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> fleet = official();
        if (((Number) fleet.get("id")).longValue() != fleetId) throw bad("Only the official fleet can be managed.");
        if (repository.count(FleetCommandQueries.ASSIGN_LEADER_SELECT_01, Map.of("id", userId)) == 0) {
            throw bad("Fleet or user not found.");
        }
        String role = payload.role() == null ? "fleet_admiral" : normalizeRole(payload.role());
        long roleId = roleId(role);
        Map<String, Object> existing = repository.optional(
                FleetCommandQueries.ASSIGN_LEADER_SELECT_02, Map.of("userId", userId)).orElse(null);
        long membershipId;
        if (existing == null) {
            membershipId = repository.insertReturningId(FleetCommandQueries.ASSIGN_LEADER_INSERT_01, Map.of("fleetId", fleetId, "userId", userId, "roleId", roleId, "now", now()));
        } else {
            membershipId = ((Number) existing.get("id")).longValue();
            repository.update(FleetCommandQueries.ASSIGN_LEADER_UPDATE_01, Map.of("fleetId", fleetId, "roleId", roleId, "now", now(), "id", membershipId));
        }
        audit.record(actor, "fleet_membership", membershipId, "update",
                "Assigned fleet leadership role " + role + " to user #" + userId + ".", List.of("role", "status"));
        return views.membership(membershipId, null);
    }

    private Map<String, Object> official() {
        return repository.optional(FleetCommandQueries.OFFICIAL_SELECT_01, Map.of()).orElseThrow(() -> bad("Official fleet not found."));
    }

    private FleetMembershipTargetDto targetMembership(long fleetId, long membershipId) {
        return repository.optional(FleetCommandQueries.TARGET_MEMBERSHIP_SELECT_01,
                        Map.of("membershipId", membershipId, "fleetId", fleetId))
                .map(mapper::membershipTarget)
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Membership not found."));
    }

    private long roleId(String code) {
        return repository.optional(FleetCommandQueries.ROLE_ID_SELECT_01, Map.of("code", code))
                .map(row -> ((Number) row.get("id")).longValue())
                .orElseThrow(() -> bad("Invalid or inactive fleet role."));
    }

    private void ensureUnique(String name, String slug, Long excludedId) {
        String exclusion = excludedId == null ? "" : FleetCommandQueries.ENSURE_UNIQUE_AND_01;
        long duplicates = repository.count(FleetCommandQueries.ENSURE_UNIQUE_SELECT_01 + exclusion, SqlParameters.ofNullable("name", name, "slug", slug, "id", excludedId));
        if (duplicates > 0) throw bad("Fleet name or slug already exists.");
    }

    private FleetMembershipUpdate normalize(FleetMembershipUpdate payload) {
        String role = payload.role() == null ? null : normalizeRole(payload.role());
        String status = payload.status() == null ? null : payload.status().strip().toLowerCase(Locale.ROOT);
        if (status != null && !STATUSES.contains(status)) throw bad("Invalid membership status.");
        return mapper.membershipUpdate(payload, role, status);
    }

    private static String focus(String value) {
        String normalized = value.strip().toLowerCase(Locale.ROOT);
        if (!FOCUS.contains(normalized)) throw bad("Invalid fleet focus.");
        return normalized;
    }

    private static String slug(String value) {
        String normalized = value.strip().toLowerCase(Locale.ROOT).replace(' ', '-');
        if (!normalized.matches("[a-z0-9][a-z0-9-]{1,119}")) throw bad("Invalid fleet slug.");
        return normalized;
    }

    private static String normalizeRole(String value) {
        String normalized = value.strip().toLowerCase(Locale.ROOT).replace('-', '_').replace(' ', '_');
        if (!normalized.matches("[a-z][a-z0-9_]{1,39}")) throw bad("Invalid fleet role.");
        return normalized;
    }

    private static String blank(String value) {
        return value == null || value.isBlank() ? null : value.strip();
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(BAD_REQUEST, message);
    }
}
