package eu.royalblackwater.api.builds.model;

public record UpgradeSlotAccess(
        int baseSlots,
        boolean slot5,
        boolean slot6,
        boolean slot7,
        boolean slot8,
        int expansionSlots,
        int researchSlots,
        int shipExtraSlots,
        int availableSlots) { }
