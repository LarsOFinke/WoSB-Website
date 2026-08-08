package eu.royalblackwater.api.builds.controller;

import eu.royalblackwater.api.builds.service.BuildPrintoutService;
import eu.royalblackwater.api.builds.service.BuildService;
import eu.royalblackwater.api.dto.BuildCreate;
import eu.royalblackwater.api.dto.BuildOptionsCatalog;
import eu.royalblackwater.api.dto.BuildPage;
import eu.royalblackwater.api.dto.BuildPrintoutRead;
import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.BuildRoleRead;
import eu.royalblackwater.api.dto.BuildUpdate;
import eu.royalblackwater.api.dto.BuildVoteState;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.core.io.Resource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@Validated
public class BuildController extends ApiControllerSupport {

    private final BuildService builds;
    private final BuildPrintoutService printouts;

    public BuildController(BuildService builds, BuildPrintoutService printouts) {
        this.builds = builds; this.printouts = printouts;
    }

    @GetMapping("/api/builds")
    public ResponseEntity<BuildPage> getBuilds(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "build_type", required = false) String buildType,
            @RequestParam(name = "classification", required = false) String classification,
            @RequestParam(name = "limit", defaultValue = "50") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.list(search,
                            buildType, classification,
                            limit, offset, actor), 200);
    }

    @PostMapping("/api/builds")
    public ResponseEntity<BuildRead> postBuild(
            @Valid @RequestBody BuildCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.create(body, actor), 201);
    }

    @GetMapping("/api/builds/mine")
    public ResponseEntity<BuildPage> getMyBuilds(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "build_type", required = false) String buildType,
            @RequestParam(name = "classification", required = false) String classification,
            @RequestParam(name = "limit", defaultValue = "50") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.mine(search,
                            buildType, classification,
                            limit, offset, actor), 200);
    }

    @DeleteMapping("/api/builds/mine/{build_id}")
    public ResponseEntity<Void> deleteMyBuild(
            @PathVariable("build_id") long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        builds.deleteOwned(buildId, actor); return noContent();
    }

    @PutMapping("/api/builds/mine/{build_id}")
    public ResponseEntity<BuildRead> putMyBuild(
            @PathVariable("build_id") long buildId,
            @Valid @RequestBody BuildUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.update(buildId,
                            body, actor), 200);
    }

    @GetMapping("/api/builds/options")
    public ResponseEntity<BuildOptionsCatalog> getBuildOptions(
            @RequestParam(name = "ship_id", required = false) Long shipId
    ) {

        CurrentUser.require();
        return respond(builds.options(shipId), 200);
    }

    @GetMapping("/api/builds/roles")
    public ResponseEntity<List<BuildRoleRead>> getBuildRoles() {
        CurrentUser.require();
        return respond(builds.roles(), 200);
    }

    @GetMapping("/api/builds/{build_id}")
    public ResponseEntity<BuildRead> getBuildDetail(
            @PathVariable("build_id") long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.get(buildId, actor), 200);
    }

    @GetMapping("/api/builds/{build_id}/printout")
    public ResponseEntity<Resource> getBuildPrintout(
            @PathVariable("build_id") long buildId,
            @RequestParam(name = "cache_key", required = true) String cacheKey
    ) {

        CurrentUser.require();
        return download(printouts.content(buildId, cacheKey));
    }

    @PutMapping(value = "/api/builds/{build_id}/printout", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<BuildPrintoutRead> putBuildPrintout(
            @PathVariable("build_id") long buildId,
            @RequestParam(name = "cache_key", required = true) String cacheKey,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            @RequestParam(name = "source_updated_at", required = true) LocalDateTime sourceUpdatedAt,
            @RequestParam(name = "notify_discord", defaultValue = "false") boolean notifyDiscord,
            @RequestPart("image") MultipartFile upload
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(printouts.save(buildId, upload, cacheKey, sourceUpdatedAt, actor), 200);
    }

    @DeleteMapping("/api/builds/{build_id}/upvote")
    public ResponseEntity<BuildVoteState> deleteBuildUpvote(
            @PathVariable("build_id") long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.vote(buildId, actor, false), 200);
    }

    @PostMapping("/api/builds/{build_id}/upvote")
    public ResponseEntity<BuildVoteState> postBuildUpvote(
            @PathVariable("build_id") long buildId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(builds.vote(buildId, actor, true), 200);
    }
}
