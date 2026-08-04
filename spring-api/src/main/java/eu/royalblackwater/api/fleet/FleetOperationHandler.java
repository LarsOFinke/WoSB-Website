package eu.royalblackwater.api.fleet;

import eu.royalblackwater.api.contract.FleetCreate;
import eu.royalblackwater.api.contract.FleetJoinRequest;
import eu.royalblackwater.api.contract.FleetMembershipUpdate;
import eu.royalblackwater.api.contract.FleetRoleCreate;
import eu.royalblackwater.api.contract.FleetRoleUpdate;
import eu.royalblackwater.api.contract.FleetUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@Component
public class FleetOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_fleets_api_fleets_get",
            "post_fleet_api_fleets_post",
            "post_fleet_join_api_fleets_join_post",
            "get_manageable_fleets_api_fleets_manageable_get",
            "get_my_fleet_memberships_api_fleets_memberships_me_get",
            "get_public_official_fleet_api_fleets_public_official_get",
            "get_fleet_detail_api_fleets__fleet_id__get",
            "put_fleet_api_fleets__fleet_id__put",
            "post_fleet_leader_api_fleets__fleet_id__leaders__user_id__post",
            "get_fleet_management_detail_api_fleets__fleet_id__manage_get",
            "put_membership_api_fleets__fleet_id__memberships__membership_id__put",
            "get_fleet_roles_api_fleets__fleet_id__roles_get",
            "post_fleet_role_api_fleets__fleet_id__roles_post",
            "delete_role_api_fleets__fleet_id__roles__role_id__delete",
            "put_fleet_role_api_fleets__fleet_id__roles__role_id__put");

    private final FleetViewService views;
    private final FleetCommandService commands;
    private final FleetRoleService roles;

    public FleetOperationHandler(FleetViewService views, FleetCommandService commands, FleetRoleService roles) {
        this.views = views;
        this.commands = commands;
        this.roles = roles;
    }

    @Override
    public Set<String> operations() {
        return OPERATIONS;
    }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody,
                             MultipartFile upload) {
        return switch (operationId) {
            case "get_public_official_fleet_api_fleets_public_official_get" -> views.officialPublic();
            case "get_fleets_api_fleets_get" -> views.list(false);
            case "get_manageable_fleets_api_fleets_manageable_get" -> views.manageable(CurrentUser.require());
            case "get_my_fleet_memberships_api_fleets_memberships_me_get" ->
                    views.membershipsFor(CurrentUser.require().id());
            case "get_fleet_detail_api_fleets__fleet_id__get" ->
                    views.detail(longParameter(parameters, "fleet_id"), false, CurrentUser.require());
            case "get_fleet_management_detail_api_fleets__fleet_id__manage_get" ->
                    views.detail(longParameter(parameters, "fleet_id"), true, CurrentUser.require());
            case "post_fleet_api_fleets_post" -> commands.create(
                    body(requestBody, FleetCreate.class), requireAdmin());
            case "put_fleet_api_fleets__fleet_id__put" -> commands.update(
                    longParameter(parameters, "fleet_id"), body(requestBody, FleetUpdate.class), CurrentUser.require());
            case "post_fleet_join_api_fleets_join_post" -> commands.join(
                    body(requestBody, FleetJoinRequest.class), CurrentUser.require());
            case "put_membership_api_fleets__fleet_id__memberships__membership_id__put" ->
                    commands.updateMembership(longParameter(parameters, "fleet_id"),
                            longParameter(parameters, "membership_id"),
                            body(requestBody, FleetMembershipUpdate.class), CurrentUser.require());
            case "post_fleet_leader_api_fleets__fleet_id__leaders__user_id__post" ->
                    commands.assignLeader(longParameter(parameters, "fleet_id"), longParameter(parameters, "user_id"),
                            body(requestBody, FleetMembershipUpdate.class), requireAdmin());
            case "get_fleet_roles_api_fleets__fleet_id__roles_get" ->
                    roles.list(booleanParameter(parameters, "include_inactive", false));
            case "post_fleet_role_api_fleets__fleet_id__roles_post" -> roles.create(
                    longParameter(parameters, "fleet_id"), body(requestBody, FleetRoleCreate.class), CurrentUser.require());
            case "put_fleet_role_api_fleets__fleet_id__roles__role_id__put" -> roles.update(
                    longParameter(parameters, "fleet_id"), longParameter(parameters, "role_id"),
                    body(requestBody, FleetRoleUpdate.class), CurrentUser.require());
            case "delete_role_api_fleets__fleet_id__roles__role_id__delete" -> {
                roles.delete(longParameter(parameters, "fleet_id"), longParameter(parameters, "role_id"),
                        CurrentUser.require());
                yield null;
            }
            default -> throw new IllegalStateException("Unsupported fleet operation: " + operationId);
        };
    }

    private static AuthenticatedUser requireAdmin() {
        AuthenticatedUser user = CurrentUser.require();
        if (!user.isAdmin()) throw new ResponseStatusException(FORBIDDEN, "Administrator access required.");
        return user;
    }
}
