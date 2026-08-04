package eu.royalblackwater.api.account;

import eu.royalblackwater.api.contract.ProfileUpdate;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class ProfileOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_profile_api_profile_get",
            "get_preference_options_api_profile_preferences_options_get",
            "put_profile_api_profile_put");
    private final UserViewService users;
    private final ProfileService profiles;

    public ProfileOperationHandler(UserViewService users, ProfileService profiles) {
        this.users = users;
        this.profiles = profiles;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        int userId = CurrentUser.require().id();
        return switch (operationId) {
            case "get_profile_api_profile_get" -> users.read(userId);
            case "get_preference_options_api_profile_preferences_options_get" -> profiles.options();
            case "put_profile_api_profile_put" -> profiles.update(userId, body(body, ProfileUpdate.class));
            default -> throw new IllegalStateException("Unsupported profile operation: " + operationId);
        };
    }
}
