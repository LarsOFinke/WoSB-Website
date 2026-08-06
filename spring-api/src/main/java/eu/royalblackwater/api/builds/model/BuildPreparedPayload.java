package eu.royalblackwater.api.builds.model;

import java.util.List;
import java.util.Map;

public record BuildPreparedPayload(
        BuildPayload payload,
        BuildShipSnapshot ship,
        BuildFeatureSnapshot researchFeature,
        List<BuildSlotSelection> slots,
        List<Map<String, Number>> effectSets,
        Map<String, Number> effects,
        UpgradeSlotAccess upgradeAccess) { }
