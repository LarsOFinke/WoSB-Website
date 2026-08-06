package eu.royalblackwater.api.builds.controller;

import eu.royalblackwater.api.dto.BuildOptionsCatalog;
import eu.royalblackwater.api.dto.BuildPage;
import eu.royalblackwater.api.dto.BuildPrintoutRead;
import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.BuildRoleRead;
import eu.royalblackwater.api.dto.BuildVoteState;
import java.util.List;
import org.springframework.core.io.Resource;
import eu.royalblackwater.api.builds.service.BuildPrintoutService;
import eu.royalblackwater.api.builds.service.BuildService;
import eu.royalblackwater.api.dto.BuildCreate;
import eu.royalblackwater.api.dto.BuildUpdate;
import eu.royalblackwater.api.contract.api.BuildsApi;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@Validated
public class BuildController extends ApiControllerSupport implements BuildsApi {

    private final BuildService builds;
    private final BuildPrintoutService printouts;

    public BuildController(BuildService builds, BuildPrintoutService printouts) {
        this.builds = builds; this.printouts = printouts;
    }

    @Override
    public ResponseEntity<BuildPage> getBuilds(
            String search,
            String buildType,
            String classification,
            long limit,
            long offset
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.list(search,
                            buildType, classification,
                            limit, offset, actor), 200);
    }

    @Override
    public ResponseEntity<BuildRead> postBuild(
            BuildCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.create(body, actor), 201);
    }

    @Override
    public ResponseEntity<BuildPage> getMyBuilds(
            String search,
            String buildType,
            String classification,
            long limit,
            long offset
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.mine(search,
                            buildType, classification,
                            limit, offset, actor), 200);
    }

    @Override
    public ResponseEntity<Void> deleteMyBuild(
            long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        builds.deleteOwned(buildId, actor); return noContent();
    }

    @Override
    public ResponseEntity<BuildRead> putMyBuild(
            long buildId,
            BuildUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.update(buildId,
                            body, actor), 200);
    }

    @Override
    public ResponseEntity<BuildOptionsCatalog> getBuildOptions(
            Long shipId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.options(shipId), 200);
    }

    @Override
    public ResponseEntity<List<BuildRoleRead>> getBuildRoles() {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.roles(), 200);
    }

    @Override
    public ResponseEntity<BuildRead> getBuildDetail(
            long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.get(buildId, actor), 200);
    }

    @Override
    public ResponseEntity<Resource> getBuildPrintout(
            long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return download(printouts.content(buildId));
    }

    @Override
    public ResponseEntity<BuildPrintoutRead> putBuildPrintout(
            long buildId,
            boolean notifyDiscord,
            MultipartFile upload
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(printouts.save(buildId, upload, actor), 200);
    }

    @Override
    public ResponseEntity<BuildVoteState> deleteBuildUpvote(
            long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.vote(buildId, actor, false), 200);
    }

    @Override
    public ResponseEntity<BuildVoteState> postBuildUpvote(
            long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.vote(buildId, actor, true), 200);
    }

    private static Long nullableLong(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name); return value instanceof Number number ? number.longValue() : null;
    }
}
