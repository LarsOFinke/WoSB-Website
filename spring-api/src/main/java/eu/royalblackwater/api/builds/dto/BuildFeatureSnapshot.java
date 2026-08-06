package eu.royalblackwater.api.builds.dto;

import java.util.Map;

public record BuildFeatureSnapshot(long id, int grantedSlots, Map<String, Number> effects) { }
