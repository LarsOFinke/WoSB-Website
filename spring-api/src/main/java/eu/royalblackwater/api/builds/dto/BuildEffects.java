package eu.royalblackwater.api.builds.dto;

import java.util.List;
import java.util.Map;

public record BuildEffects(List<Map<String, Number>> sets, Map<String, Number> totals) { }
