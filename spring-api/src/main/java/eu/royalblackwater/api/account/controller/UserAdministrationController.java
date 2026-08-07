package eu.royalblackwater.api.account.controller;

import eu.royalblackwater.api.account.filter.UserAdministrationFilter;
import eu.royalblackwater.api.account.service.UserAdministrationService;
import eu.royalblackwater.api.dto.ModeratorCreate;
import eu.royalblackwater.api.dto.ModeratorCreateResponse;
import eu.royalblackwater.api.dto.UserAdministrationUpdate;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class UserAdministrationController extends ApiControllerSupport {

    private final UserAdministrationService users;

    public UserAdministrationController(UserAdministrationService users) {
        this.users = users;
    }

    @PostMapping("/api/admin/moderators")
    public ResponseEntity<ModeratorCreateResponse> adminCreateModerator(
            @Valid @RequestBody ModeratorCreate body
    ) {
        return respond(users.createModerator(body,CurrentUser.require()), 201);
    }

    @GetMapping("/api/admin/users")
    public ResponseEntity<List<UserRead>> adminListUsers(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "role", required = false) String role,
            @RequestParam(name = "status", required = false) String status,
            @RequestParam(name = "fleet_id", required = false) Long fleetId,
            @RequestParam(name = "limit", defaultValue = "100") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {
        return respond(users.list(UserAdministrationFilter.from(
                search, role, status, fleetId, limit, offset)), 200);
    }

    @PutMapping("/api/admin/users/{user_id}")
    public ResponseEntity<UserRead> adminUpdateUser(
            @PathVariable("user_id") long userId,
            @Valid @RequestBody UserAdministrationUpdate body
    ) {

        return respond(users.update(
                            userId,body,CurrentUser.require()), 200);
    }
}
