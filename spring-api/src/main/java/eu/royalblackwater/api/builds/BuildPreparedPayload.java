package eu.royalblackwater.api.builds;

import java.util.List;
import java.util.Map;

record BuildPreparedPayload(
        BuildPayload payload,
        BuildShipSnapshot ship,
        BuildFeatureSnapshot researchFeature,
        List<BuildSlotSelection> slots,
        List<Map<String, Number>> effectSets,
        Map<String, Number> effects,
        UpgradeSlotAccess upgradeAccess) { }

record BuildSlotSelection(String type, int index, long optionId, String optionName, int quantity,
                          BuildCatalogOption option) { }

record UpgradeSlotAccess(int baseSlots, boolean slot5, boolean slot6, boolean slot7, boolean slot8,
                         int expansionSlots, int researchSlots, int shipExtraSlots, int availableSlots) { }
