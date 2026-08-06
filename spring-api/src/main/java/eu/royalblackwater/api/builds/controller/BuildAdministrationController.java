package eu.royalblackwater.api.builds.controller;

import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.BuildRoleRead;
import java.util.List;
import eu.royalblackwater.api.builds.service.BuildRoleAdministrationService;
import eu.royalblackwater.api.builds.service.BuildService;
import eu.royalblackwater.api.dto.BuildRoleAssignment;
import eu.royalblackwater.api.dto.BuildRoleCreate;
import eu.royalblackwater.api.dto.BuildRoleUpdate;
import eu.royalblackwater.api.contract.api.AdminBuildRolesApi;
import eu.royalblackwater.api.contract.api.AdminBuildsApi;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class BuildAdministrationController extends ApiControllerSupport implements AdminBuildRolesApi, AdminBuildsApi {

    private final BuildService builds;
    private final BuildRoleAdministrationService roles;

    public BuildAdministrationController(BuildService builds, BuildRoleAdministrationService roles) {
        this.builds = builds; this.roles = roles;
    }

    @Override
    public ResponseEntity<List<BuildRoleRead>> adminListBuildRoles() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(roles.list(), 200);
    }

    @Override
    public ResponseEntity<BuildRoleRead> adminCreateBuildRole(
            BuildRoleCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(roles.create(body, actor), 201);
    }

    @Override
    public ResponseEntity<Void> adminDeleteBuildRole(
            String slug
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        roles.delete(slug, actor); return noContent();
    }

    @Override
    public ResponseEntity<BuildRoleRead> adminUpdateBuildRole(
            String slug,
            BuildRoleUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(roles.update(slug,
                            body, actor), 200);
    }

    @Override
    public ResponseEntity<List<BuildRead>> adminListBuilds(
            String search,
            String buildType
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.allForAdministration(actor), 200);
    }

    @Override
    public ResponseEntity<Void> adminDeleteBuild(
            long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        builds.deleteAny(buildId, actor); return noContent();
    }

    @Override
    public ResponseEntity<BuildRead> adminAssignBuildRole(
            long buildId,
            BuildRoleAssignment body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.assignRole(buildId,
                            body.buildType(), actor), 200);
    }
}
