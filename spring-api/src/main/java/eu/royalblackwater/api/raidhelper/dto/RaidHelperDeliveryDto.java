package eu.royalblackwater.api.raidhelper.dto;

/** Complete typed delivery work item loaded from the Raid-Helper persistence boundary. */
public record RaidHelperDeliveryDto(
        long linkId,
        String operation,
        String externalEventId,
        String leaderIdOverride,
        String defaultLeaderId,
        String serverId,
        String channelId,
        boolean destinationActive,
        boolean profileActive,
        boolean templateActive,
        RaidHelperConnectionDto connection,
        RaidHelperEventDto event,
        RaidHelperTemplateConfigDto template) {
}
