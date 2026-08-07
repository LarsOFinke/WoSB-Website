package eu.royalblackwater.api.fleet.controller;

import eu.royalblackwater.api.dto.FleetCreate;
import eu.royalblackwater.api.dto.FleetDetail;
import eu.royalblackwater.api.dto.FleetJoinRequest;
import eu.royalblackwater.api.dto.FleetMembershipRead;
import eu.royalblackwater.api.dto.FleetMembershipSelfRead;
import eu.royalblackwater.api.dto.FleetMembershipUpdate;
import eu.royalblackwater.api.dto.FleetPublicRead;
import eu.royalblackwater.api.dto.FleetRead;
import eu.royalblackwater.api.dto.FleetRoleCreate;
import eu.royalblackwater.api.dto.FleetRoleRead;
import eu.royalblackwater.api.dto.FleetRoleUpdate;
import eu.royalblackwater.api.dto.FleetUpdate;
import eu.royalblackwater.api.fleet.service.FleetCommandService;
import eu.royalblackwater.api.fleet.service.FleetRoleService;
import eu.royalblackwater.api.fleet.service.FleetViewService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
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
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@RestController
@Validated
public class FleetController extends ApiControllerSupport {

    private final FleetViewService views;
    private final FleetCommandService commands;
    private final FleetRoleService roles;

    public FleetController(FleetViewService views, FleetCommandService commands, FleetRoleService roles) {
        this.views = views;
        this.commands = commands;
        this.roles = roles;
    }

    @GetMapping("/api/fleets")
    public ResponseEntity<List<FleetRead>> getFleets() {
        return respond(views.list(false), 200);
    }

    @PostMapping("/api/fleets")
    public ResponseEntity<FleetRead> postFleet(
            @Valid @RequestBody FleetCreate body
    ) {
        return respond(commands.create(
                            body, requireAdmin()), 201);
    }

    @PostMapping("/api/fleets/join")
    public ResponseEntity<FleetMembershipRead> postFleetJoin(
            @Valid @RequestBody FleetJoinRequest body
    ) {
        return respond(commands.join(
                            body, CurrentUser.require()), 201);
    }

    @GetMapping("/api/fleets/manageable")
    public ResponseEntity<List<FleetRead>> getManageableFleets() {
        return respond(views.manageable(CurrentUser.require()), 200);
    }

    @GetMapping("/api/fleets/memberships/me")
    public ResponseEntity<List<FleetMembershipSelfRead>> getMyFleetMemberships() {
        return respond(views.membershipsFor(CurrentUser.require().id()), 200);
    }

    @GetMapping("/api/fleets/public/official")
    public ResponseEntity<FleetPublicRead> getPublicOfficialFleet() {
        return respond(views.officialPublic(), 200);
    }

    @GetMapping("/api/fleets/{fleet_id}")
    public ResponseEntity<FleetDetail> getFleetDetail(
            @PathVariable("fleet_id") long fleetId
    ) {

        return respond(views.detail(fleetId, false, CurrentUser.require()), 200);
    }

    @PutMapping("/api/fleets/{fleet_id}")
    public ResponseEntity<FleetRead> putFleet(
            @PathVariable("fleet_id") long fleetId,
            @Valid @RequestBody FleetUpdate body
    ) {

        return respond(commands.update(
                            fleetId, body, CurrentUser.require()), 200);
    }

    @PostMapping("/api/fleets/{fleet_id}/leaders/{user_id}")
    public ResponseEntity<FleetMembershipRead> postFleetLeader(
            @PathVariable("fleet_id") long fleetId,
            @PathVariable("user_id") long userId,
            @Valid @RequestBody FleetMembershipUpdate body
    ) {

        return respond(commands.assignLeader(fleetId, userId,
                                    body, requireAdmin()), 200);
    }

    @GetMapping("/api/fleets/{fleet_id}/manage")
    public ResponseEntity<FleetDetail> getFleetManagementDetail(
            @PathVariable("fleet_id") long fleetId
    ) {

        return respond(views.detail(fleetId, true, CurrentUser.require()), 200);
    }

    @PutMapping("/api/fleets/{fleet_id}/memberships/{membership_id}")
    public ResponseEntity<FleetMembershipRead> putMembership(
            @PathVariable("fleet_id") long fleetId,
            @PathVariable("membership_id") long membershipId,
            @Valid @RequestBody FleetMembershipUpdate body
    ) {

        return respond(commands.updateMembership(fleetId,
                                    membershipId,
                                    body, CurrentUser.require()), 200);
    }

    @GetMapping("/api/fleets/{fleet_id}/roles")
    public ResponseEntity<List<FleetRoleRead>> getFleetRoles(
            @PathVariable("fleet_id") long fleetId,
            @RequestParam(name = "include_inactive", defaultValue = "false") boolean includeInactive
    ) {

        return respond(roles.list(fleetId, includeInactive, CurrentUser.require()), 200);
    }

    @PostMapping("/api/fleets/{fleet_id}/roles")
    public ResponseEntity<FleetRoleRead> postFleetRole(
            @PathVariable("fleet_id") long fleetId,
            @Valid @RequestBody FleetRoleCreate body
    ) {

        return respond(roles.create(
                            fleetId, body, CurrentUser.require()), 201);
    }

    @DeleteMapping("/api/fleets/{fleet_id}/roles/{role_id}")
    public ResponseEntity<Void> deleteRole(
            @PathVariable("fleet_id") long fleetId,
            @PathVariable("role_id") long roleId
    ) {

        roles.delete(fleetId, roleId,
                CurrentUser.require());
        return noContent();
    }

    @PutMapping("/api/fleets/{fleet_id}/roles/{role_id}")
    public ResponseEntity<FleetRoleRead> putFleetRole(
            @PathVariable("fleet_id") long fleetId,
            @PathVariable("role_id") long roleId,
            @Valid @RequestBody FleetRoleUpdate body
    ) {

        return respond(roles.update(
                            fleetId, roleId,
                            body, CurrentUser.require()), 200);
    }

    private static AuthenticatedUser requireAdmin() {
        AuthenticatedUser user = CurrentUser.require();
        if (!user.isAdmin()) throw new ResponseStatusException(FORBIDDEN, "Administrator access required.");
        return user;
    }
}
