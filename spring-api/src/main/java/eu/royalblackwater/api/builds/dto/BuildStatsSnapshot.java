package eu.royalblackwater.api.builds.dto;

import eu.royalblackwater.api.dto.BuildStatRow;
import java.util.List;
import java.util.Map;

/** Typed calculation result before transport mapping. */
public record BuildStatsSnapshot(

        long ammunitionSlotsUsed,
        Long baseCrewCapacity,
        Long baseSailorMinimum,
        Long baseSailorTarget,
        Map<String, Number> baseStats,
        Long baseUpgradeSlotsAvailable,
        long consumableSlotsUsed,
        long crewCapacity,
        long crewRemaining,
        long crewTotal,
        Long effectiveCrewCapacity,
        Long effectiveSailorMinimum,
        Long effectiveSailorTarget,
        Map<String, Number> effectiveStats,
        Long expansionUpgradeSlots,
        Long extraUpgradeSlots,
        long holdSlotsUsed,
        long inventorySlotsUsed,
        Map<String, Number> itemEffects,
        Map<String, Number> lanternEffects,
        Map<String, Number> mortarModificationEffects,
        Boolean mortarModificationInstalled,
        Map<String, Number> researchUpgradeSlotEffects,
        Long researchUpgradeSlots,
        Map<String, Number> sailEffects,
        Long sailingEfficiencyPct,
        long sailorMinimum,
        Long sailorTarget,
        boolean sailorsRequiredMet,
        Long shipExtraUpgradeSlots,
        Map<String, Number> specialCrewEffects,
        long specialCrewTotal,
        List<BuildStatRow> statRows,
        List<String> statWarnings,
        Map<String, Number> upgradeBuffs,
        Map<String, Number> upgradeDebuffs,
        Map<String, Number> upgradeEffects,
        Boolean upgradeSlot5Unlocked,
        Boolean upgradeSlot6Available,
        Boolean upgradeSlot6Unlocked,
        Boolean upgradeSlot7Available,
        Boolean upgradeSlot8Available,
        long upgradeSlotsAvailable,
        long upgradeSlotsUsed,
        Map<String, Long> weaponCapacity,
        Long weaponCapacityTotal,
        Map<String, Long> weaponSlots,
        long weaponTotal
) { }
