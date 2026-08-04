package eu.royalblackwater.api.groups;

import eu.royalblackwater.api.contract.GroupCreate;
import eu.royalblackwater.api.contract.GroupJoinRequest;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class GroupOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_groups_api_groups_get",
            "post_group_api_groups_post",
            "get_my_groups_api_groups_mine_get",
            "get_group_detail_api_groups__group_id__get",
            "post_group_close_api_groups__group_id__close_post",
            "post_group_join_api_groups__group_id__join_post");
    private final GroupService groups;

    public GroupOperationHandler(GroupService groups) {
        this.groups = groups;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody,
                             MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "get_groups_api_groups_get" -> groups.list(
                    stringParameter(parameters, "search"), stringParameter(parameters, "focus"),
                    nullableLong(parameters, "min_ship_rate"), nullableLong(parameters, "max_ship_rate"), null);
            case "post_group_api_groups_post" -> groups.create(body(requestBody, GroupCreate.class), actor);
            case "get_my_groups_api_groups_mine_get" -> groups.list(
                    stringParameter(parameters, "search"), null, null, null, actor.id());
            case "get_group_detail_api_groups__group_id__get" -> groups.get(longParameter(parameters, "group_id"));
            case "post_group_join_api_groups__group_id__join_post" -> groups.join(
                    longParameter(parameters, "group_id"), body(requestBody, GroupJoinRequest.class), actor);
            case "post_group_close_api_groups__group_id__close_post" -> {
                groups.close(longParameter(parameters, "group_id"), actor);
                yield null;
            }
            default -> throw new IllegalStateException("Unsupported group operation: " + operationId);
        };
    }

    private static Long nullableLong(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        return value instanceof Number number ? number.longValue() : null;
    }
}
