package eu.royalblackwater.api.raidhelper.dto;

/** Decrypted-at-use connection metadata for one Raid-Helper profile. */
public record RaidHelperConnectionDto(
        String apiBaseUrl,
        String apiKeyEncrypted,
        String serverId) {
}
