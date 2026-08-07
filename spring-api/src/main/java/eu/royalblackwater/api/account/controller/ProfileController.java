package eu.royalblackwater.api.account.controller;

import eu.royalblackwater.api.account.service.ProfileService;
import eu.royalblackwater.api.account.service.UserViewService;
import eu.royalblackwater.api.dto.ProfilePreferenceOptionsRead;
import eu.royalblackwater.api.dto.ProfileUpdate;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class ProfileController extends ApiControllerSupport {

    private final UserViewService users;
    private final ProfileService profiles;

    public ProfileController(UserViewService users, ProfileService profiles) {
        this.users = users;
        this.profiles = profiles;
    }

    @GetMapping("/api/profile")
    public ResponseEntity<UserRead> getProfile() {
        int userId = CurrentUser.require().id();
        return respond(users.read(userId), 200);
    }

    @PutMapping("/api/profile")
    public ResponseEntity<UserRead> putProfile(
            @Valid @RequestBody ProfileUpdate body
    ) {
        int userId = CurrentUser.require().id();
        return respond(profiles.update(userId, body), 200);
    }

    @GetMapping("/api/profile/preferences/options")
    public ResponseEntity<ProfilePreferenceOptionsRead> getPreferenceOptions() {
        return respond(profiles.options(), 200);
    }
}
