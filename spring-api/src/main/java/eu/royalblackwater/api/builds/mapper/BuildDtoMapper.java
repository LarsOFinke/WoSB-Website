package eu.royalblackwater.api.builds.mapper;

import eu.royalblackwater.api.builds.dto.BuildStatDefinition;
import eu.royalblackwater.api.builds.dto.BuildStatsSnapshot;
import eu.royalblackwater.api.dto.BuildPrintoutRead;
import eu.royalblackwater.api.dto.BuildRoleRead;
import eu.royalblackwater.api.dto.BuildStatRow;
import eu.royalblackwater.api.dto.BuildVoteState;
import eu.royalblackwater.api.dto.BuildStatDefinitionRead;
import eu.royalblackwater.api.dto.ShipStats;
import eu.royalblackwater.api.persistence.RowValues;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

public final class BuildDtoMapper {
    private BuildDtoMapper() { }

    public static BuildRoleRead role(Map<String, Object> row) {
        return new BuildRoleRead(RowValues.dateTime(row, "created_at"), RowValues.string(row, "description"),
                RowValues.requiredString(row, "label"), RowValues.requiredString(row, "slug"),
                RowValues.longValue(row, "sort_order"), RowValues.dateTime(row, "updated_at"));
    }
    public static BuildVoteState voteState(long buildId, boolean selected, long count) {
        return new BuildVoteState(buildId, selected, count);
    }

    public static BuildStatRow statRow(Number base, String category, String effectKey, Number effective,
                                       Number flatModifier, boolean debuff, String key, String label,
                                       Number modifier, String modifierKind, Number percentModifier,
                                       long precision, String source, String unit) {
        return new BuildStatRow(base, category, effectKey, effective, flatModifier, debuff, key, label,
                modifier, modifierKind, percentModifier, precision, source, unit);
    }

    public static BuildStatRow unknownStatRow(String key, String label, Number value, boolean debuff,
                                              long precision, String unit) {
        return new BuildStatRow(null, "upgrade_modifiers", key, value, value, debuff, key, label, value,
                "flat", null, precision, "upgrade_modifiers", unit);
    }

    public static BuildPrintoutRead printout(boolean changed, String cacheKey, String checksum, long size,
            LocalDateTime sourceUpdatedAt, LocalDateTime updatedAt, String url) {
        return new BuildPrintoutRead(changed, cacheKey, checksum, size, sourceUpdatedAt, updatedAt, url);
    }

    public static BuildStatDefinitionRead statDefinition(BuildStatDefinition definition) {
        return new BuildStatDefinitionRead(definition.baseField(), definition.calculationFlatEffect(),
                definition.category(), definition.flatEffect(), definition.key(), definition.label(),
                definition.pctBaseField(), definition.pctEffect(), definition.positiveIsGood(),
                (long) definition.precision(), definition.source(), definition.unit());
    }

    public static ShipStats shipStats(BuildStatsSnapshot value) {
        return new ShipStats(
                value.ammunitionSlotsUsed(),
                value.baseCrewCapacity(),
                value.baseSailorMinimum(),
                value.baseSailorTarget(),
                new LinkedHashMap<String, Object>(value.baseStats()),
                value.baseUpgradeSlotsAvailable(),
                value.consumableSlotsUsed(),
                value.crewCapacity(),
                value.crewRemaining(),
                value.crewTotal(),
                value.effectiveCrewCapacity(),
                value.effectiveSailorMinimum(),
                value.effectiveSailorTarget(),
                value.effectiveStats(),
                value.expansionUpgradeSlots(),
                value.extraUpgradeSlots(),
                value.holdSlotsUsed(),
                value.inventorySlotsUsed(),
                value.itemEffects(),
                value.lanternEffects(),
                value.mortarModificationEffects(),
                value.mortarModificationInstalled(),
                value.researchUpgradeSlotEffects(),
                value.researchUpgradeSlots(),
                value.sailEffects(),
                value.sailingEfficiencyPct(),
                value.sailorMinimum(),
                value.sailorTarget(),
                value.sailorsRequiredMet(),
                value.shipExtraUpgradeSlots(),
                value.specialCrewEffects(),
                value.specialCrewTotal(),
                value.statRows(),
                value.statWarnings(),
                value.upgradeBuffs(),
                value.upgradeDebuffs(),
                value.upgradeEffects(),
                value.upgradeSlot5Unlocked(),
                value.upgradeSlot6Available(),
                value.upgradeSlot6Unlocked(),
                value.upgradeSlot7Available(),
                value.upgradeSlot8Available(),
                value.upgradeSlotsAvailable(),
                value.upgradeSlotsUsed(),
                value.weaponCapacity(),
                value.weaponCapacityTotal(),
                value.weaponSlots(),
                value.weaponTotal());
    }

}
