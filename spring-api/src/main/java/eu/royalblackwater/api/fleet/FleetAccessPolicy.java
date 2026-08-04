package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.contract.FleetMembershipManagementRead;
import eu.royalblackwater.api.contract.FleetMembershipUpdate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class FleetAccessPolicy {
    private final JdbcQueryService jdbc;

    public FleetAccessPolicy(JdbcQueryService jdbc) {
        this.jdbc = jdbc;
    }

    public Set<Long> managedFleetIds(AuthenticatedUser actor, List<Long> fleetIds) {
        if (fleetIds == null || fleetIds.isEmpty()) return Set.of();
        if (actor.staff()) return Set.copyOf(fleetIds);
        Set<Long> result = new LinkedHashSet<>();
        for (Map<String, Object> row : jdbc.query("""
                select distinct m.fleet_id
                from fleet_memberships m join fleet_roles r on r.id=m.fleet_role_id
                where m.fleet_id in (:fleetIds) and m.user_id=:userId and m.status='active'
                  and r.can_manage_fleet=true and r.is_active=true
                """, Map.of("fleetIds", fleetIds, "userId", actor.id()))) {
            result.add(((Number) row.get("fleet_id")).longValue());
        }
        return Set.copyOf(result);
    }

    public boolean canManageFleet(AuthenticatedUser actor, long fleetId) {
        if (actor.staff()) return true;
        return jdbc.count("""
                select count(*)
                from fleet_memberships m join fleet_roles r on r.id = m.fleet_role_id
                where m.fleet_id = :fleetId and m.user_id = :userId and m.status = 'active'
                  and r.can_manage_fleet = true and r.is_active = true
                """, Map.of("fleetId", fleetId, "userId", actor.id())) > 0;
    }

    public void requireFleetManager(AuthenticatedUser actor, long fleetId) {
        if (!canManageFleet(actor, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN, "Fleet leadership access required.");
        }
    }

    public void requireRoleManager(AuthenticatedUser actor, long fleetId) {
        if (actor.isAdmin()) return;
        long allowed = jdbc.count("""
                select count(*)
                from fleet_memberships m join fleet_roles r on r.id = m.fleet_role_id
                where m.fleet_id = :fleetId and m.user_id = :userId and m.status = 'active'
                  and r.code = 'fleet_admiral'
                """, Map.of("fleetId", fleetId, "userId", actor.id()));
        if (allowed == 0) {
            throw new ResponseStatusException(FORBIDDEN,
                    "Fleet admiral access required to manage fleet roles.");
        }
    }

    public void validateMembershipUpdate(AuthenticatedUser actor, long fleetId,
                                         Map<String, Object> target, FleetMembershipUpdate payload) {
        FleetMembershipManagementRead allowed = permissions(actor, fleetId, target);
        boolean directoryChange = payload.note() != null || payload.assignment() != null || payload.adminNote() != null;
        if (directoryChange && !Boolean.TRUE.equals(allowed.canEditDirectory())) {
            throw new ResponseStatusException(FORBIDDEN, "You cannot edit this protected fleet membership.");
        }
        if (payload.status() != null && !Boolean.TRUE.equals(allowed.canChangeStatus())) {
            String message = "last_admiral".equals(allowed.reason())
                    ? "The last active fleet admiral cannot be deactivated."
                    : "You cannot change the status of this protected fleet membership.";
            throw new ResponseStatusException(FORBIDDEN, message);
        }
        if (payload.role() != null) {
            if (!Boolean.TRUE.equals(allowed.canChangeRole())) {
                String message = "last_admiral".equals(allowed.reason())
                        ? "The last active fleet admiral cannot be demoted."
                        : "You cannot change the role of this protected fleet membership.";
                throw new ResponseStatusException(FORBIDDEN, message);
            }
            if (allowed.assignableRoles() == null || !allowed.assignableRoles().contains(payload.role())) {
                throw new ResponseStatusException(FORBIDDEN, "You cannot assign this fleet role.");
            }
        }
    }

    public FleetMembershipManagementRead permissions(
            AuthenticatedUser actor, long fleetId, Map<String, Object> target) {
        long targetUserId = ((Number) target.get("user_id")).longValue();
        String targetRole = String.valueOf(target.get("role"));
        long targetRank = ((Number) target.get("role_rank")).longValue();
        String targetStatus = String.valueOf(target.get("status"));
        String targetSiteRole = String.valueOf(target.get("site_role"));
        long activeAdmirals = activeAdmirals(fleetId);
        boolean lastAdmiral = "fleet_admiral".equals(targetRole)
                && "active".equals(targetStatus) && activeAdmirals <= 1;
        List<String> allRoles = assignableRoles(Long.MAX_VALUE);

        if (actor.isAdmin()) {
            return result(true, !lastAdmiral, !lastAdmiral, allRoles,
                    lastAdmiral ? "last_admiral" : null);
        }
        if (targetUserId == actor.id()) return result(false, false, false, List.of(), "self");
        if ("admin".equals(targetSiteRole)) return result(false, false, false, List.of(), "site_admin");
        if ("moderator".equals(targetSiteRole)) return result(false, false, false, List.of(), "site_peer");
        if ("fleet_admiral".equals(targetRole)) return result(false, false, false, List.of(), "fleet_admiral");

        if ("moderator".equals(actor.role())) {
            long admiralRank = roleRank("fleet_admiral", 80);
            return result(true, true, true, assignableRoles(admiralRank), null);
        }
        Map<String, Object> membership = actorMembership(actor.id(), fleetId);
        if (membership != null && Boolean.TRUE.equals(membership.get("can_manage_members"))) {
            long actorRank = ((Number) membership.get("rank")).longValue();
            if (targetRank >= actorRank) return result(false, false, false, List.of(), "fleet_peer");
            return result(true, true, true, assignableRoles(actorRank), null);
        }
        return result(false, false, false, List.of(), "insufficient");
    }

    private Map<String, Object> actorMembership(int userId, long fleetId) {
        return jdbc.optional("""
                select r.rank, r.can_manage_members
                from fleet_memberships m join fleet_roles r on r.id = m.fleet_role_id
                where m.user_id = :userId and m.fleet_id = :fleetId and m.status = 'active'
                """, Map.of("userId", userId, "fleetId", fleetId)).orElse(null);
    }

    private long activeAdmirals(long fleetId) {
        return jdbc.count("""
                select count(*) from fleet_memberships m join fleet_roles r on r.id = m.fleet_role_id
                where m.fleet_id = :fleetId and m.status = 'active' and r.code = 'fleet_admiral'
                """, Map.of("fleetId", fleetId));
    }

    private long roleRank(String code, long fallback) {
        return jdbc.optional("select rank from fleet_roles where code = :code", Map.of("code", code))
                .map(row -> ((Number) row.get("rank")).longValue()).orElse(fallback);
    }

    private List<String> assignableRoles(long belowRank) {
        return jdbc.query("""
                select code from fleet_roles where is_active = true and rank < :rank
                order by rank asc, code asc
                """, Map.of("rank", belowRank)).stream().map(row -> String.valueOf(row.get("code"))).toList();
    }

    private static FleetMembershipManagementRead result(
            boolean edit, boolean role, boolean status, List<String> assignable, String reason) {
        return new FleetMembershipManagementRead(
                assignable, role, status, edit, reason != null || !(edit || role || status), reason);
    }
}
