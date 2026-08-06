package eu.royalblackwater.api.builds.model;

import java.util.List;
import java.util.Map;

public record BuildAggregate(Map<String, Object> row, List<String> classifications, List<BuildStoredSlot> slots) { }
