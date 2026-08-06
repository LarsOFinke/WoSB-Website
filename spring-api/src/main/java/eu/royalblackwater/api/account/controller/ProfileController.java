package eu.royalblackwater.api.account.controller;

import eu.royalblackwater.api.dto.ProfilePreferenceOptionsRead;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.account.service.ProfileService;
import eu.royalblackwater.api.account.service.UserViewService;
import eu.royalblackwater.api.dto.ProfileUpdate;
import eu.royalblackwater.api.contract.api.ProfileApi;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class ProfileController extends ApiControllerSupport implements ProfileApi {

    private final UserViewService users;
    private final ProfileService profiles;

    public ProfileController(UserViewService users, ProfileService profiles) {
        this.users = users;
        this.profiles = profiles;
    }

    @Override
    public ResponseEntity<UserRead> getProfile() {
        int userId = CurrentUser.require().id();
        return respond(users.read(userId), 200);
    }

    @Override
    public ResponseEntity<UserRead> putProfile(
            ProfileUpdate body
    ) {
        int userId = CurrentUser.require().id();
        return respond(profiles.update(userId, body), 200);
    }

    @Override
    public ResponseEntity<ProfilePreferenceOptionsRead> getPreferenceOptions() {
        int userId = CurrentUser.require().id();
        return respond(profiles.options(), 200);
    }
}
