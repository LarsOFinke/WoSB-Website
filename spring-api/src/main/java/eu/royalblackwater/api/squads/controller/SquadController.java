package eu.royalblackwater.api.squads.controller;

import eu.royalblackwater.api.dto.SquadCreate;
import eu.royalblackwater.api.dto.SquadDetailRead;
import eu.royalblackwater.api.dto.SquadMemberCreate;
import eu.royalblackwater.api.dto.SquadMemberUpdate;
import eu.royalblackwater.api.dto.SquadRosterMemberRead;
import eu.royalblackwater.api.dto.SquadSummaryRead;
import eu.royalblackwater.api.dto.SquadUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.squads.filter.SquadListFilter;
import eu.royalblackwater.api.squads.service.SquadService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class SquadController extends ApiControllerSupport {
    private final SquadService squads;

    public SquadController(SquadService squads) {
        this.squads = squads;
    }

    @GetMapping("/api/squads")
    public ResponseEntity<List<SquadSummaryRead>> getSquads(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "fleet_id", required = false) Long fleetId,
            @RequestParam(name = "include_inactive", defaultValue = "false") boolean includeInactive,
            @RequestParam(name = "limit", defaultValue = "100") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {
        return respond(squads.list(actor(),
                SquadListFilter.from(search, fleetId, includeInactive, limit, offset)), 200);
    }

    @PostMapping("/api/squads")
    public ResponseEntity<SquadDetailRead> postSquad(
            @Valid @RequestBody SquadCreate body
    ) {
        return respond(squads.create(body, actor()), 201);
    }

    @GetMapping("/api/squads/mine")
    public ResponseEntity<List<SquadSummaryRead>> getMySquads() {
        return respond(squads.list(actor(), SquadListFilter.mine()), 200);
    }

    @GetMapping("/api/squads/roster")
    public ResponseEntity<List<SquadRosterMemberRead>> getSquadRoster() {
        return respond(squads.roster(actor()), 200);
    }

    @DeleteMapping("/api/squads/{squad_id}")
    public ResponseEntity<Void> deleteSquad(
            @PathVariable("squad_id") long squadId
    ) {
        squads.archive(squadId, actor());
        return noContent();
    }

    @GetMapping("/api/squads/{squad_id}")
    public ResponseEntity<SquadDetailRead> getSquadDetail(
            @PathVariable("squad_id") long squadId
    ) {
        return respond(squads.get(squadId, actor()), 200);
    }

    @PutMapping("/api/squads/{squad_id}")
    public ResponseEntity<SquadDetailRead> putSquad(
            @PathVariable("squad_id") long squadId,
            @Valid @RequestBody SquadUpdate body
    ) {
        return respond(squads.update(squadId, body, actor()), 200);
    }

    @PostMapping("/api/squads/{squad_id}/members")
    public ResponseEntity<SquadDetailRead> postSquadMember(
            @PathVariable("squad_id") long squadId,
            @Valid @RequestBody SquadMemberCreate body
    ) {
        return respond(squads.addMember(squadId, body, actor()), 201);
    }

    @DeleteMapping("/api/squads/{squad_id}/members/{member_id}")
    public ResponseEntity<SquadDetailRead> deleteSquadMember(
            @PathVariable("squad_id") long squadId,
            @PathVariable("member_id") long memberId
    ) {
        return respond(squads.removeMember(squadId, memberId, actor()), 200);
    }

    @PutMapping("/api/squads/{squad_id}/members/{member_id}")
    public ResponseEntity<SquadDetailRead> putSquadMember(
            @PathVariable("squad_id") long squadId,
            @PathVariable("member_id") long memberId,
            @Valid @RequestBody SquadMemberUpdate body
    ) {
        return respond(squads.updateMember(squadId, memberId, body, actor()), 200);
    }

    private static AuthenticatedUser actor() {
        return CurrentUser.require();
    }
}
