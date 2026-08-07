package eu.royalblackwater.api.builds.controller;

import eu.royalblackwater.api.builds.service.BuildRoleAdministrationService;
import eu.royalblackwater.api.builds.service.BuildService;
import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.BuildRoleAssignment;
import eu.royalblackwater.api.dto.BuildRoleCreate;
import eu.royalblackwater.api.dto.BuildRoleRead;
import eu.royalblackwater.api.dto.BuildRoleUpdate;
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

@RestController
@Validated
public class BuildAdministrationController extends ApiControllerSupport {

    private final BuildService builds;
    private final BuildRoleAdministrationService roles;

    public BuildAdministrationController(BuildService builds, BuildRoleAdministrationService roles) {
        this.builds = builds; this.roles = roles;
    }

    @GetMapping("/api/admin/build-roles")
    public ResponseEntity<List<BuildRoleRead>> adminListBuildRoles() {
        CurrentUser.require();
        return respond(roles.list(), 200);
    }

    @PostMapping("/api/admin/build-roles")
    public ResponseEntity<BuildRoleRead> adminCreateBuildRole(
            @Valid @RequestBody BuildRoleCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(roles.create(body, actor), 201);
    }

    @DeleteMapping("/api/admin/build-roles/{slug}")
    public ResponseEntity<Void> adminDeleteBuildRole(
            @PathVariable("slug") String slug
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        roles.delete(slug, actor); return noContent();
    }

    @PutMapping("/api/admin/build-roles/{slug}")
    public ResponseEntity<BuildRoleRead> adminUpdateBuildRole(
            @PathVariable("slug") String slug,
            @Valid @RequestBody BuildRoleUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(roles.update(slug,
                            body, actor), 200);
    }

    @GetMapping("/api/admin/builds")
    public ResponseEntity<List<BuildRead>> adminListBuilds(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "build_type", required = false) String buildType
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.allForAdministration(actor), 200);
    }

    @DeleteMapping("/api/admin/builds/{build_id}")
    public ResponseEntity<Void> adminDeleteBuild(
            @PathVariable("build_id") long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        builds.deleteAny(buildId, actor); return noContent();
    }

    @PutMapping("/api/admin/builds/{build_id}/role")
    public ResponseEntity<BuildRead> adminAssignBuildRole(
            @PathVariable("build_id") long buildId,
            @Valid @RequestBody BuildRoleAssignment body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.assignRole(buildId,
                            body.buildType(), actor), 200);
    }
}
