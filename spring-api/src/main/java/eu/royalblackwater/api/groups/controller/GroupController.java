package eu.royalblackwater.api.groups.controller;

import eu.royalblackwater.api.dto.GroupRead;
import java.util.List;
import eu.royalblackwater.api.dto.GroupCreate;
import eu.royalblackwater.api.dto.GroupJoinRequest;
import eu.royalblackwater.api.contract.api.GroupsApi;
import eu.royalblackwater.api.groups.service.GroupService;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class GroupController extends ApiControllerSupport implements GroupsApi {

    private final GroupService groups;

    public GroupController(GroupService groups) {
        this.groups = groups;
    }

    @Override
    public ResponseEntity<List<GroupRead>> getGroups(
            String search,
            String focus,
            Long minShipRate,
            Long maxShipRate
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.list(
                            search, focus,
                            minShipRate, maxShipRate, null), 200);
    }

    @Override
    public ResponseEntity<GroupRead> postGroup(
            GroupCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.create(body, actor), 201);
    }

    @Override
    public ResponseEntity<List<GroupRead>> getMyGroups(
            String search
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.list(
                            search, null, null, null, actor.id()), 200);
    }

    @Override
    public ResponseEntity<GroupRead> getGroupDetail(
            long groupId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.get(groupId), 200);
    }

    @Override
    public ResponseEntity<Void> postGroupClose(
            long groupId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        groups.close(groupId, actor);
        return noContent();
    }

    @Override
    public ResponseEntity<GroupRead> postGroupJoin(
            long groupId,
            GroupJoinRequest body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(groups.join(
                            groupId, body, actor), 200);
    }

    private static Long nullableLong(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        return value instanceof Number number ? number.longValue() : null;
    }
}
