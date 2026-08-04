package eu.royalblackwater.api.account;

import eu.royalblackwater.api.fleet.FleetMembershipEntity;
import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper
public interface UserMapper {
    @Mapping(target = "displayName", expression = "java(displayName(user))")
    @Mapping(target = "role", source = "user.siteRole.code")
    @Mapping(target = "isActive", source = "user.active")
    @Mapping(target = "isBootstrapAdmin", source = "user.bootstrapAdmin")
    @Mapping(target = "canGrantAdmin", expression = "java(canGrantAdmin(user))")
    @Mapping(target = "fleetName", expression = "java(fleetName(user, membership))")
    @Mapping(target = "fleetId", source = "membership.fleet.id")
    @Mapping(target = "fleetMembershipId", source = "membership.id")
    @Mapping(target = "fleetMembershipStatus", source = "membership.status")
    @Mapping(target = "fleetMembershipRole", source = "membership.fleetRole.code")
    @Mapping(target = "preferredFocus", source = "user.profile.preferredFocus")
    @Mapping(target = "availability", source = "user.profile.availability")
    @Mapping(target = "timezone", source = "user.profile.timezone")
    @Mapping(target = "discordHandle", source = "user.profile.discordHandle")
    @Mapping(target = "preferredShipIds", source = "preferredShipIds")
    @Mapping(target = "preferredRoleIds", source = "preferredRoleIds")
    @Mapping(target = "note", source = "user.profile.note")
    AuthContracts.UserRead toRead(
            UserEntity user,
            FleetMembershipEntity membership,
            List<Long> preferredShipIds,
            List<Long> preferredRoleIds);

    default String displayName(UserEntity user) {
        return user.getProfile() == null || user.getProfile().getDisplayName() == null
                ? user.getUsername() : user.getProfile().getDisplayName();
    }

    default String fleetName(UserEntity user, FleetMembershipEntity membership) {
        if (membership != null && membership.getFleet() != null) {
            return membership.getFleet().getName();
        }
        return user.getProfile() == null ? null : user.getProfile().getExternalFleetName();
    }

    default boolean canGrantAdmin(UserEntity user) {
        return user.isBootstrapAdmin() && "admin".equals(user.getSiteRole().getCode());
    }
}
