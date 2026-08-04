package eu.royalblackwater.api.account;

import eu.royalblackwater.api.contract.ModeratorCreate;
import eu.royalblackwater.api.contract.UserAdministrationUpdate;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class UserAdministrationOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "admin_list_users_api_admin_users_get",
            "admin_update_user_api_admin_users__user_id__put",
            "admin_create_moderator_api_admin_moderators_post");
    private final UserAdministrationService users;

    public UserAdministrationOperationHandler(UserAdministrationService users) {
        this.users = users;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return switch (operationId) {
            case "admin_list_users_api_admin_users_get" -> users.list(UserAdministrationFilter.from(parameters));
            case "admin_update_user_api_admin_users__user_id__put" -> users.update(
                    longParameter(parameters,"user_id"),body(body,UserAdministrationUpdate.class),CurrentUser.require());
            case "admin_create_moderator_api_admin_moderators_post" ->
                    users.createModerator(body(body,ModeratorCreate.class),CurrentUser.require());
            default -> throw new IllegalStateException("Unsupported user administration operation: " + operationId);
        };
    }
}
