package eu.royalblackwater.api.groups.controller;

import eu.royalblackwater.api.dto.GroupCreate;
import eu.royalblackwater.api.dto.GroupJoinRequest;
import eu.royalblackwater.api.dto.GroupRead;
import eu.royalblackwater.api.groups.service.GroupService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class GroupController extends ApiControllerSupport {

    private final GroupService groups;

    public GroupController(GroupService groups) {
        this.groups = groups;
    }

    @GetMapping("/api/groups")
    public ResponseEntity<List<GroupRead>> getGroups(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "focus", required = false) String focus,
            @RequestParam(name = "min_ship_rate", required = false) Long minShipRate,
            @RequestParam(name = "max_ship_rate", required = false) Long maxShipRate
    ) {

        CurrentUser.require();
        return respond(groups.list(
                            search, focus,
                            minShipRate, maxShipRate, null), 200);
    }

    @PostMapping("/api/groups")
    public ResponseEntity<GroupRead> postGroup(
            @Valid @RequestBody GroupCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.create(body, actor), 201);
    }

    @GetMapping("/api/groups/mine")
    public ResponseEntity<List<GroupRead>> getMyGroups(
            @RequestParam(name = "search", required = false) String search
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.list(
                            search, null, null, null, actor.id()), 200);
    }

    @GetMapping("/api/groups/{group_id}")
    public ResponseEntity<GroupRead> getGroupDetail(
            @PathVariable("group_id") long groupId
    ) {

        CurrentUser.require();
        return respond(groups.get(groupId), 200);
    }

    @PostMapping("/api/groups/{group_id}/close")
    public ResponseEntity<Void> postGroupClose(
            @PathVariable("group_id") long groupId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        groups.close(groupId, actor);
        return noContent();
    }

    @PostMapping("/api/groups/{group_id}/join")
    public ResponseEntity<GroupRead> postGroupJoin(
            @PathVariable("group_id") long groupId,
            @Valid @RequestBody GroupJoinRequest body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.join(
                            groupId, body, actor), 200);
    }
}
