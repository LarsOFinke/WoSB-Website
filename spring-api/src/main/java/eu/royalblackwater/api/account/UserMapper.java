package eu.royalblackwater.api.account;

import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper
public interface UserMapper {
    @Mapping(target = "displayName", expression = "java(displayName(user))")
    @Mapping(target = "role", source = "siteRole.code")
    @Mapping(target = "isActive", source = "active")
    @Mapping(target = "isBootstrapAdmin", source = "bootstrapAdmin")
    @Mapping(target = "canGrantAdmin", expression = "java(user.isBootstrapAdmin() && \"admin\".equals(user.getSiteRole().getCode()))")
    @Mapping(target = "fleetName", source = "profile.externalFleetName")
    @Mapping(target = "fleetId", ignore = true)
    @Mapping(target = "fleetMembershipId", ignore = true)
    @Mapping(target = "fleetMembershipStatus", ignore = true)
    @Mapping(target = "fleetMembershipRole", ignore = true)
    @Mapping(target = "preferredFocus", source = "profile.preferredFocus")
    @Mapping(target = "availability", source = "profile.availability")
    @Mapping(target = "timezone", source = "profile.timezone")
    @Mapping(target = "discordHandle", source = "profile.discordHandle")
    @Mapping(target = "preferredShipIds", expression = "java(java.util.List.of())")
    @Mapping(target = "preferredRoleIds", expression = "java(java.util.List.of())")
    @Mapping(target = "note", source = "profile.note")
    AuthContracts.UserRead toRead(UserEntity user);

    default String displayName(UserEntity user) {
        return user.getProfile() == null ? user.getUsername() : user.getProfile().getDisplayName();
    }
}
