package eu.royalblackwater.api.squads.service;

import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.squads.repository.SquadRepository;
import eu.royalblackwater.api.squads.repository.queries.SquadAccessQueries;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class SquadAccessPolicy {
    private final SquadRepository repository;
    private final FleetAccessPolicy fleets;

    public SquadAccessPolicy(SquadRepository repository, FleetAccessPolicy fleets) {
        this.repository = repository;
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
        return repository.count(SquadAccessQueries.HAS_MANAGED_SQUAD_SELECT_01, Map.of("userId", actor.id())) > 0;
    }

    private java.util.Optional<String> memberRole(int userId, long squadId) {
        return repository.optional(SquadAccessQueries.MEMBER_ROLE_SELECT_01, Map.of("squadId", squadId, "userId", userId))
                .map(row -> String.valueOf(row.get("code")));
    }
}
