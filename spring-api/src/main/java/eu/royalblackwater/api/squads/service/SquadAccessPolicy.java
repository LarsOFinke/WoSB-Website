package eu.royalblackwater.api.squads.service;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class SquadAccessPolicy {
    public boolean canManage(AuthenticatedUser actor, long squadId, long fleetId) {
        return actor.staff();
    }

    public boolean canAdminister(AuthenticatedUser actor, long squadId, long fleetId) {
        return actor.staff();
    }

    public void requireManage(AuthenticatedUser actor, long squadId, long fleetId) {
        if (!canManage(actor, squadId, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN, "Moderator access required to manage squads.");
        }
    }

    public void requireAdminister(AuthenticatedUser actor, long squadId, long fleetId) {
        if (!canAdminister(actor, squadId, fleetId)) {
            throw new ResponseStatusException(FORBIDDEN,
                    "Moderator access required to change squad command roles.");
        }
    }
}
