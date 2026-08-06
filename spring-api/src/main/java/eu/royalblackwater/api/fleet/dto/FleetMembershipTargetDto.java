package eu.royalblackwater.api.fleet.dto;

/** Internal DTO describing the protected membership attributes needed by authorization rules. */
public record FleetMembershipTargetDto(
        long userId,
        String role,
        long roleRank,
        String status,
        String siteRole) {
}
