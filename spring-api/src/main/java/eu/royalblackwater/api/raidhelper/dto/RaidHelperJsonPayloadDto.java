package eu.royalblackwater.api.raidhelper.dto;

import java.util.LinkedHashMap;
import java.util.Map;

/** Typed boundary wrapper for the intentionally dynamic Raid-Helper JSON request object. */
public record RaidHelperJsonPayloadDto(Map<String, Object> values) {
    public RaidHelperJsonPayloadDto {
        values = values == null ? Map.of() : Map.copyOf(new LinkedHashMap<>(values));
    }

    public static RaidHelperJsonPayloadDto of(Map<String, Object> values) {
        return new RaidHelperJsonPayloadDto(values);
    }
}
