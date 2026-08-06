package eu.royalblackwater.api.builds.model;

import java.util.Map;

public record BuildFeatureSnapshot(long id, int grantedSlots, Map<String, Number> effects) { }
