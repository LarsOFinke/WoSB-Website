package eu.royalblackwater.api.builds;

import java.util.Map;

record BuildFeatureSnapshot(long id, int grantedSlots, Map<String, Number> effects) { }
