package eu.royalblackwater.api.account.controller;

import eu.royalblackwater.api.dto.ModeratorCreateResponse;
import eu.royalblackwater.api.dto.UserRead;
import java.util.List;
import eu.royalblackwater.api.account.filter.UserAdministrationFilter;
import eu.royalblackwater.api.account.service.UserAdministrationService;
import eu.royalblackwater.api.dto.ModeratorCreate;
import eu.royalblackwater.api.dto.UserAdministrationUpdate;
import eu.royalblackwater.api.contract.api.AdminModeratorsApi;
import eu.royalblackwater.api.contract.api.AdminUsersApi;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.shared.web.RequestParameters;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class UserAdministrationController extends ApiControllerSupport implements AdminModeratorsApi, AdminUsersApi {

    private final UserAdministrationService users;

    public UserAdministrationController(UserAdministrationService users) {
        this.users = users;
    }

    @Override
    public ResponseEntity<ModeratorCreateResponse> adminCreateModerator(
            ModeratorCreate body
    ) {
        return respond(users.createModerator(body(body,ModeratorCreate.class),CurrentUser.require()), 201);
    }

    @Override
    public ResponseEntity<List<UserRead>> adminListUsers(
            String search,
            String role,
            String status,
            Long fleetId,
            long limit,
            long offset
    ) {
        Map<String, Object> parameters = RequestParameters.of("search", search, "role", role, "status", status, "fleet_id", fleetId, "limit", limit, "offset", offset);
        return respond(users.list(UserAdministrationFilter.from(parameters)), 200);
    }

    @Override
    public ResponseEntity<UserRead> adminUpdateUser(
            long userId,
            UserAdministrationUpdate body
    ) {

        return respond(users.update(
                            userId,body(body,UserAdministrationUpdate.class),CurrentUser.require()), 200);
    }
}
