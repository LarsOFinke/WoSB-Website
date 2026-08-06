package eu.royalblackwater.api.raidhelper.dto;

/** Internal destination configuration passed between Raid-Helper services. */
public record RaidHelperDestinationConfigDto(
        long id,
        long profileId,
        String channelId,
        RaidHelperConnectionDto connection,
        String timezone,
        String defaultLeaderId,
        Long squadId,
        String squadName) {
}
