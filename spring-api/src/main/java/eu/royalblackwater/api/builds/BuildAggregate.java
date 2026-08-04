package eu.royalblackwater.api.builds;

import java.util.List;
import java.util.Map;

record BuildAggregate(Map<String, Object> row, List<String> classifications, List<BuildStoredSlot> slots) { }
record BuildStoredSlot(String type, int index, long optionId, String optionName, int quantity) { }
record BuildPageResult(List<BuildAggregate> items, long total, long limit, long offset) { }
