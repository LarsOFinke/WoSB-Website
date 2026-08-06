package eu.royalblackwater.api.account.mapper;

import eu.royalblackwater.api.account.entity.UserEntity;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import org.springframework.stereotype.Component;

@Component
public class AuthenticationDtoMapper {
    public AuthenticatedUser toAuthenticatedUser(UserEntity user) {
        return new AuthenticatedUser(
                user.getId(),
                user.getUsername(),
                user.getSiteRole().getCode(),
                user.getSiteRole().isStaff(),
                user.getSiteRole().canManageSystem(),
                user.isBootstrapAdmin());
    }
}
