package eu.royalblackwater.api.raidhelper.dto;

/** Internal rendering configuration for a Raid-Helper event template. */
public record RaidHelperTemplateConfigDto(
        long id,
        long profileId,
        boolean active,
        String timezone,
        String raidTemplateId,
        String titleTemplate,
        String descriptionTemplate,
        String announcementTemplate,
        String payloadTemplateJson) {
}
