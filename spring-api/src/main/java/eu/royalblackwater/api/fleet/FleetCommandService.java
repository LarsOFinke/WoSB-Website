package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.FleetCreate;
import eu.royalblackwater.api.contract.FleetJoinRequest;
import eu.royalblackwater.api.contract.FleetMembershipRead;
import eu.royalblackwater.api.contract.FleetMembershipUpdate;
import eu.royalblackwater.api.contract.FleetRead;
import eu.royalblackwater.api.contract.FleetUpdate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.persistence.SqlUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
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
    private final JdbcQueryService jdbc;
    private final FleetViewService views;
    private final FleetAccessPolicy policy;
    private final AuditService audit;
    private final Clock clock;

    public FleetCommandService(JdbcQueryService jdbc, FleetViewService views, FleetAccessPolicy policy,
                               AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.views = views;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional
    public FleetRead create(FleetCreate payload, AuthenticatedUser actor) {
        if (jdbc.count("select count(*) from fleets", Map.of()) > 0) {
            throw bad("The official fleet is already configured.");
        }
        String focus = focus(payload.focus());
        String name = payload.name().strip();
        String slug = slug(payload.slug());
        ensureUnique(name, slug, null);
        long id = jdbc.insertReturningId("""
                insert into fleets
                    (name, slug, focus, description, standing_orders, sort_order, is_active, created_at, updated_at)
                values (:name, :slug, :focus, :description, :standingOrders, :sortOrder, :active, :now, :now)
                returning id
                """, SqlParameters.ofNullable(
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
        Map<String, Object> existing = jdbc.optional("select * from fleets where id=:id", Map.of("id", fleetId))
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
            jdbc.update(update.sql(), update.parameters());
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
        Map<String, Object> existing = jdbc.optional(
                "select id, status from fleet_memberships where user_id=:userId", Map.of("userId", actor.id()))
                .orElse(null);
        long membershipId;
        if (existing == null) {
            membershipId = jdbc.insertReturningId("""
                    insert into fleet_memberships
                        (fleet_id, user_id, fleet_role_id, status, note, joined_at, updated_at)
                    values (:fleetId, :userId, :roleId, 'pending', :note, :now, :now)
                    returning id
                    """, SqlParameters.ofNullable(
                            "fleetId", fleetId, "userId", actor.id(), "roleId", roleId,
                            "note", blank(payload.note()), "now", now()));
        } else {
            membershipId = ((Number) existing.get("id")).longValue();
            String status = "inactive".equals(existing.get("status")) ? "pending" : String.valueOf(existing.get("status"));
            jdbc.update("""
                    update fleet_memberships set fleet_id=:fleetId, status=:status, note=:note, updated_at=:now
                    where id=:id
                    """, SqlParameters.ofNullable(
                            "fleetId", fleetId, "status", status, "note", blank(payload.note()),
                            "now", now(), "id", membershipId));
        }
        return views.membership(membershipId, null);
    }

    @Transactional
    public FleetMembershipRead updateMembership(long fleetId, long membershipId,
                                                 FleetMembershipUpdate payload, AuthenticatedUser actor) {
        policy.requireFleetManager(actor, fleetId);
        Map<String, Object> target = targetMembership(fleetId, membershipId);
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
            jdbc.update(update.sql(), update.parameters());
            audit.record(actor, "fleet_membership", membershipId, "update",
                    "Updated fleet membership for user #" + target.get("user_id") + ".", update.columns());
        }
        return views.membership(membershipId, actor);
    }

    @Transactional
    public FleetMembershipRead assignLeader(long fleetId, long userId,
                                             FleetMembershipUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> fleet = official();
        if (((Number) fleet.get("id")).longValue() != fleetId) throw bad("Only the official fleet can be managed.");
        if (jdbc.count("select count(*) from users where id=:id", Map.of("id", userId)) == 0) {
            throw bad("Fleet or user not found.");
        }
        String role = payload.role() == null ? "fleet_admiral" : normalizeRole(payload.role());
        long roleId = roleId(role);
        Map<String, Object> existing = jdbc.optional(
                "select id from fleet_memberships where user_id=:userId", Map.of("userId", userId)).orElse(null);
        long membershipId;
        if (existing == null) {
            membershipId = jdbc.insertReturningId("""
                    insert into fleet_memberships
                        (fleet_id, user_id, fleet_role_id, status, joined_at, updated_at)
                    values (:fleetId, :userId, :roleId, 'active', :now, :now) returning id
                    """, Map.of("fleetId", fleetId, "userId", userId, "roleId", roleId, "now", now()));
        } else {
            membershipId = ((Number) existing.get("id")).longValue();
            jdbc.update("""
                    update fleet_memberships
                    set fleet_id=:fleetId, fleet_role_id=:roleId, status='active', updated_at=:now
                    where id=:id
                    """, Map.of("fleetId", fleetId, "roleId", roleId, "now", now(), "id", membershipId));
        }
        audit.record(actor, "fleet_membership", membershipId, "update",
                "Assigned fleet leadership role " + role + " to user #" + userId + ".", List.of("role", "status"));
        return views.membership(membershipId, null);
    }

    private Map<String, Object> official() {
        return jdbc.optional("""
                select * from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end, sort_order, id limit 1
                """, Map.of()).orElseThrow(() -> bad("Official fleet not found."));
    }

    private Map<String, Object> targetMembership(long fleetId, long membershipId) {
        return jdbc.optional("""
                select m.*, r.code as role, r.rank as role_rank, sr.code as site_role
                from fleet_memberships m join fleet_roles r on r.id=m.fleet_role_id
                join users u on u.id=m.user_id join site_roles sr on sr.id=u.site_role_id
                where m.id=:membershipId and m.fleet_id=:fleetId
                """, Map.of("membershipId", membershipId, "fleetId", fleetId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Membership not found."));
    }

    private long roleId(String code) {
        return jdbc.optional("select id from fleet_roles where code=:code and is_active=true", Map.of("code", code))
                .map(row -> ((Number) row.get("id")).longValue())
                .orElseThrow(() -> bad("Invalid or inactive fleet role."));
    }

    private void ensureUnique(String name, String slug, Long excludedId) {
        String exclusion = excludedId == null ? "" : " and id<>:id";
        long duplicates = jdbc.count("""
                select count(*) from fleets
                where (lower(name)=lower(:name) or slug=:slug)
                """ + exclusion, SqlParameters.ofNullable("name", name, "slug", slug, "id", excludedId));
        if (duplicates > 0) throw bad("Fleet name or slug already exists.");
    }

    private static FleetMembershipUpdate normalize(FleetMembershipUpdate payload) {
        String role = payload.role() == null ? null : normalizeRole(payload.role());
        String status = payload.status() == null ? null : payload.status().strip().toLowerCase(Locale.ROOT);
        if (status != null && !STATUSES.contains(status)) throw bad("Invalid membership status.");
        return new FleetMembershipUpdate(payload.adminNote(), payload.assignment(), payload.note(), role, status);
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
