package eu.royalblackwater.api.squads.controller;

import eu.royalblackwater.api.dto.SquadDetailRead;
import eu.royalblackwater.api.dto.SquadRosterMemberRead;
import eu.royalblackwater.api.dto.SquadSummaryRead;
import java.util.List;
import eu.royalblackwater.api.dto.SquadCreate;
import eu.royalblackwater.api.dto.SquadMemberCreate;
import eu.royalblackwater.api.dto.SquadMemberUpdate;
import eu.royalblackwater.api.dto.SquadUpdate;
import eu.royalblackwater.api.contract.api.SquadsApi;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.shared.web.RequestParameters;
import eu.royalblackwater.api.squads.filter.SquadListFilter;
import eu.royalblackwater.api.squads.service.SquadService;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class SquadController extends ApiControllerSupport implements SquadsApi {
    private final SquadService squads;

    public SquadController(SquadService squads) {
        this.squads = squads;
    }

    @Override
    public ResponseEntity<List<SquadSummaryRead>> getSquads(String search, Long fleetId, boolean includeInactive, long limit, long offset) {
        Map<String, Object> parameters = RequestParameters.of(
                "search", search,
                "fleet_id", fleetId,
                "include_inactive", includeInactive,
                "limit", limit,
                "offset", offset);
        return respond(squads.list(actor(), SquadListFilter.from(parameters)), 200);
    }

    @Override
    public ResponseEntity<SquadDetailRead> postSquad(SquadCreate body) {
        return respond(squads.create(body, actor()), 201);
    }

    @Override
    public ResponseEntity<List<SquadSummaryRead>> getMySquads() {
        return respond(squads.list(actor(), SquadListFilter.mine()), 200);
    }

    @Override
    public ResponseEntity<List<SquadRosterMemberRead>> getSquadRoster() {
        return respond(squads.roster(actor()), 200);
    }

    @Override
    public ResponseEntity<Void> deleteSquad(long squadId) {
        squads.archive(squadId, actor());
        return noContent();
    }

    @Override
    public ResponseEntity<SquadDetailRead> getSquadDetail(long squadId) {
        return respond(squads.get(squadId, actor()), 200);
    }

    @Override
    public ResponseEntity<SquadDetailRead> putSquad(long squadId, SquadUpdate body) {
        return respond(squads.update(squadId, body, actor()), 200);
    }

    @Override
    public ResponseEntity<SquadDetailRead> postSquadMember(long squadId, SquadMemberCreate body) {
        return respond(squads.addMember(squadId, body, actor()), 201);
    }

    @Override
    public ResponseEntity<SquadDetailRead> deleteSquadMember(long squadId, long memberId) {
        return respond(squads.removeMember(squadId, memberId, actor()), 200);
    }

    @Override
    public ResponseEntity<SquadDetailRead> putSquadMember(long squadId, long memberId, SquadMemberUpdate body) {
        return respond(squads.updateMember(squadId, memberId, body, actor()), 200);
    }

    private static AuthenticatedUser actor() {
        return CurrentUser.require();
    }
}
