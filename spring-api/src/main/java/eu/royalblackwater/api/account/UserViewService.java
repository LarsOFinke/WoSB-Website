package eu.royalblackwater.api.account;

import eu.royalblackwater.api.fleet.FleetMembershipEntity;
import eu.royalblackwater.api.fleet.FleetMembershipRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class UserViewService {
    private final UserRepository users;
    private final FleetMembershipRepository memberships;
    private final UserMapper mapper;

    public UserViewService(UserRepository users, FleetMembershipRepository memberships, UserMapper mapper) {
        this.users = users;
        this.memberships = memberships;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public AuthContracts.UserRead read(int userId) {
        UserEntity user = users.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "User not found."));
        FleetMembershipEntity primary = memberships.findProfileMemberships(userId).stream().findFirst().orElse(null);
        List<Long> shipIds = user.getProfile() == null ? List.of() : user.getProfile().getShipPreferences().stream()
                .map(preference -> preference.getShipId().longValue()).toList();
        List<Long> roleIds = user.getProfile() == null ? List.of() : user.getProfile().getRolePreferences().stream()
                .map(preference -> preference.getFleetRoleId().longValue()).toList();
        return mapper.toRead(user, primary, shipIds, roleIds);
    }
}
