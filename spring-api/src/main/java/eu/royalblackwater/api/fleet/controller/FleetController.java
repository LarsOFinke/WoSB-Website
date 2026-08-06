package eu.royalblackwater.api.fleet.controller;

import eu.royalblackwater.api.dto.FleetDetail;
import eu.royalblackwater.api.dto.FleetMembershipRead;
import eu.royalblackwater.api.dto.FleetMembershipSelfRead;
import eu.royalblackwater.api.dto.FleetPublicRead;
import eu.royalblackwater.api.dto.FleetRead;
import eu.royalblackwater.api.dto.FleetRoleRead;
import java.util.List;
import eu.royalblackwater.api.dto.FleetCreate;
import eu.royalblackwater.api.dto.FleetJoinRequest;
import eu.royalblackwater.api.dto.FleetMembershipUpdate;
import eu.royalblackwater.api.dto.FleetRoleCreate;
import eu.royalblackwater.api.dto.FleetRoleUpdate;
import eu.royalblackwater.api.dto.FleetUpdate;
import eu.royalblackwater.api.contract.api.FleetsApi;
import eu.royalblackwater.api.fleet.service.FleetCommandService;
import eu.royalblackwater.api.fleet.service.FleetRoleService;
import eu.royalblackwater.api.fleet.service.FleetViewService;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@RestController
@Validated
public class FleetController extends ApiControllerSupport implements FleetsApi {

    private final FleetViewService views;
    private final FleetCommandService commands;
    private final FleetRoleService roles;

    public FleetController(FleetViewService views, FleetCommandService commands, FleetRoleService roles) {
        this.views = views;
        this.commands = commands;
        this.roles = roles;
    }

    @Override
    public ResponseEntity<List<FleetRead>> getFleets() {
        return respond(views.list(false), 200);
    }

    @Override
    public ResponseEntity<FleetRead> postFleet(
            FleetCreate body
    ) {
        return respond(commands.create(
                            body, requireAdmin()), 201);
    }

    @Override
    public ResponseEntity<FleetMembershipRead> postFleetJoin(
            FleetJoinRequest body
    ) {
        return respond(commands.join(
                            body, CurrentUser.require()), 201);
    }

    @Override
    public ResponseEntity<List<FleetRead>> getManageableFleets() {
        return respond(views.manageable(CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<List<FleetMembershipSelfRead>> getMyFleetMemberships() {
        return respond(views.membershipsFor(CurrentUser.require().id()), 200);
    }

    @Override
    public ResponseEntity<FleetPublicRead> getPublicOfficialFleet() {
        return respond(views.officialPublic(), 200);
    }

    @Override
    public ResponseEntity<FleetDetail> getFleetDetail(
            long fleetId
    ) {

        return respond(views.detail(fleetId, false, CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<FleetRead> putFleet(
            long fleetId,
            FleetUpdate body
    ) {

        return respond(commands.update(
                            fleetId, body, CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<FleetMembershipRead> postFleetLeader(
            long fleetId,
            long userId,
            FleetMembershipUpdate body
    ) {

        return respond(commands.assignLeader(fleetId, userId,
                                    body, requireAdmin()), 200);
    }

    @Override
    public ResponseEntity<FleetDetail> getFleetManagementDetail(
            long fleetId
    ) {

        return respond(views.detail(fleetId, true, CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<FleetMembershipRead> putMembership(
            long fleetId,
            long membershipId,
            FleetMembershipUpdate body
    ) {

        return respond(commands.updateMembership(fleetId,
                                    membershipId,
                                    body, CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<List<FleetRoleRead>> getFleetRoles(
            long fleetId,
            boolean includeInactive
    ) {

        return respond(roles.list(includeInactive), 200);
    }

    @Override
    public ResponseEntity<FleetRoleRead> postFleetRole(
            long fleetId,
            FleetRoleCreate body
    ) {

        return respond(roles.create(
                            fleetId, body, CurrentUser.require()), 201);
    }

    @Override
    public ResponseEntity<Void> deleteRole(
            long fleetId,
            long roleId
    ) {

        roles.delete(fleetId, roleId,
                CurrentUser.require());
        return noContent();
    }

    @Override
    public ResponseEntity<FleetRoleRead> putFleetRole(
            long fleetId,
            long roleId,
            FleetRoleUpdate body
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
