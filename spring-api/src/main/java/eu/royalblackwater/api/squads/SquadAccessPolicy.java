package eu.royalblackwater.api.squads;

import eu.royalblackwater.api.fleet.FleetAccessPolicy;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class SquadAccessPolicy {
    private final JdbcQueryService jdbc;
    private final FleetAccessPolicy fleets;

    public SquadAccessPolicy(JdbcQueryService jdbc, FleetAccessPolicy fleets) {
        this.jdbc = jdbc;
        this.fleets = fleets;
    }

    public boolean canManage(AuthenticatedUser actor, long squadId, long fleetId) {
        if (fleets.canManageFleet(actor, fleetId)) return true;
        return memberRole(actor.id(), squadId).map(role -> "leader".equals(role) || "officer".equals(role)).orElse(false);
    }

    public boolean canAdminister(AuthenticatedUser actor, long squadId, long fleetId) {
        if (fleets.canManageFleet(actor, fleetId)) return true;
        return memberRole(actor.id(), squadId).map("leader"::equals).orElse(false);
    }

    public void requireManage(AuthenticatedUser actor, long squadId, long fleetId) {
        if (!canManage(actor, squadId, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN, "Squad leadership access required.");
        }
    }

    public void requireAdminister(AuthenticatedUser actor, long squadId, long fleetId) {
        if (!canAdminister(actor, squadId, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN,
                    "Only squad or fleet leadership can change command roles.");
        }
    }

    public boolean hasManagedSquad(AuthenticatedUser actor) {
        return jdbc.count("""
                select count(*) from squad_members sm
                join squads s on s.id=sm.squad_id
                join squad_roles sr on sr.id=sm.squad_role_id
                join fleet_memberships fm on fm.id=sm.fleet_membership_id
                where fm.user_id=:userId and fm.status='active' and s.is_active=true
                  and sr.code in ('leader','officer')
                """, Map.of("userId", actor.id())) > 0;
    }

    private java.util.Optional<String> memberRole(int userId, long squadId) {
        return jdbc.optional("""
                select sr.code from squad_members sm
                join squad_roles sr on sr.id=sm.squad_role_id
                join fleet_memberships fm on fm.id=sm.fleet_membership_id
                where sm.squad_id=:squadId and fm.user_id=:userId and fm.status='active'
                """, Map.of("squadId", squadId, "userId", userId))
                .map(row -> String.valueOf(row.get("code")));
    }
}
