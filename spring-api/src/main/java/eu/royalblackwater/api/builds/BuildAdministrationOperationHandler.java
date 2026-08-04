package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.contract.BuildRoleAssignment;
import eu.royalblackwater.api.contract.BuildRoleCreate;
import eu.royalblackwater.api.contract.BuildRoleUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class BuildAdministrationOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "admin_list_builds_api_admin_builds_get", "admin_list_build_roles_api_admin_build_roles_get",
            "admin_create_build_role_api_admin_build_roles_post", "admin_update_build_role_api_admin_build_roles__slug__put",
            "admin_delete_build_role_api_admin_build_roles__slug__delete", "admin_assign_build_role_api_admin_builds__build_id__role_put",
            "admin_delete_build_api_admin_builds__build_id__delete");
    private final BuildService builds;
    private final BuildRoleAdministrationService roles;

    public BuildAdministrationOperationHandler(BuildService builds, BuildRoleAdministrationService roles) {
        this.builds = builds; this.roles = roles;
    }

    @Override public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody, MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "admin_list_builds_api_admin_builds_get" -> builds.allForAdministration(actor);
            case "admin_list_build_roles_api_admin_build_roles_get" -> roles.list();
            case "admin_create_build_role_api_admin_build_roles_post" -> roles.create(body(requestBody, BuildRoleCreate.class), actor);
            case "admin_update_build_role_api_admin_build_roles__slug__put" -> roles.update(stringParameter(parameters, "slug"),
                    body(requestBody, BuildRoleUpdate.class), actor);
            case "admin_delete_build_role_api_admin_build_roles__slug__delete" -> { roles.delete(stringParameter(parameters, "slug"), actor); yield null; }
            case "admin_assign_build_role_api_admin_builds__build_id__role_put" -> builds.assignRole(longParameter(parameters, "build_id"),
                    body(requestBody, BuildRoleAssignment.class).buildType(), actor);
            case "admin_delete_build_api_admin_builds__build_id__delete" -> { builds.deleteAny(longParameter(parameters, "build_id"), actor); yield null; }
            default -> throw new IllegalStateException("Unsupported build administration operation: " + operationId);
        };
    }
}
