package eu.royalblackwater.api.strategies.dto;

import java.util.Set;

public record PreparedStrategyOverlay(
        String json,
        Set<Long> shipIds,
        Set<Long> buildIds,
        Set<Long> guideIds,
        Set<StrategyBuildReference> buildReferences) { }
