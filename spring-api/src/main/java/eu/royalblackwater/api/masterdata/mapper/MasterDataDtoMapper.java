package eu.royalblackwater.api.masterdata.mapper;

import eu.royalblackwater.api.builds.service.BuildStatCatalog;
import eu.royalblackwater.api.dto.MasterDataCategoryRead;
import eu.royalblackwater.api.dto.MasterDataOptionRead;
import eu.royalblackwater.api.dto.MasterDataOverview;
import eu.royalblackwater.api.dto.MasterDataSeedRestoreSummary;
import eu.royalblackwater.api.dto.MasterDataShipMortarModification;
import eu.royalblackwater.api.dto.MasterDataShipMount;
import eu.royalblackwater.api.dto.MasterDataShipRead;
import eu.royalblackwater.api.dto.MasterDataShipUpgradeOverrideRead;
import eu.royalblackwater.api.dto.MasterDataTaxonomyRead;
import eu.royalblackwater.api.dto.MasterDataWeaponPerformance;
import eu.royalblackwater.api.dto.ShipRateWeaponClassRuleRead;
import eu.royalblackwater.api.dto.StatEffectDefinitionRead;
import eu.royalblackwater.api.dto.WeaponClassRead;
import eu.royalblackwater.api.dto.WeaponSlotTypeRead;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

import static eu.royalblackwater.api.persistence.RowValues.dateTime;
import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.nullableLong;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.persistence.RowValues.string;

@Component
public class MasterDataDtoMapper {
    public MasterDataOverview overview(long categoryCount, long optionCount, long shipCount,
            long weaponClassCount, long slotTypeCount) {
        return new MasterDataOverview(categoryCount, optionCount, shipCount, weaponClassCount, slotTypeCount);
    }

    public MasterDataCategoryRead category(Map<String, Object> row) {
        return new MasterDataCategoryRead(
                dateTime(row, "created_at"),
                longValue(row, "id"),
                nullableBoolean(row, "is_active"),
                nullableBoolean(row, "is_seed_overridden"),
                requiredString(row, "key"),
                requiredString(row, "label"),
                string(row, "seed_key"),
                string(row, "seed_revision"),
                seedStatus(row),
                nullableLong(row, "sort_order"),
                dateTime(row, "updated_at"));
    }

    public MasterDataOptionRead option(Map<String, Object> row, Map<Long, List<String>> slots,
            Map<Long, Map<String, Double>> effects) {
        long id = longValue(row, "id");
        MasterDataWeaponPerformance performance = row.get("base_damage") == null ? null
                : new MasterDataWeaponPerformance(number(row, "base_damage"), number(row, "reload_seconds"));
        return new MasterDataOptionRead(
                slots.getOrDefault(id, List.of()),
                longValue(row, "category_id"),
                requiredString(row, "category_key"),
                requiredString(row, "category_label"),
                dateTime(row, "created_at"),
                id,
                string(row, "image_url"),
                nullableBoolean(row, "is_active"),
                nullableBoolean(row, "is_seed_overridden"),
                requiredString(row, "name"),
                string(row, "notes"),
                string(row, "option_kind"),
                string(row, "seed_key"),
                string(row, "seed_revision"),
                seedStatus(row),
                nullableLong(row, "sort_order"),
                string(row, "source"),
                effects.getOrDefault(id, Map.of()),
                dateTime(row, "updated_at"),
                nullableDouble(row, "weapon_caliber_inches"),
                string(row, "weapon_class"),
                performance);
    }

    public MasterDataShipRead ship(Map<String, Object> row, List<Map<String, Object>> mounts,
            Map<String, Object> mortar, List<Map<String, Object>> overrideRows,
            Map<Long, Map<String, Double>> baseEffects) {
        return new MasterDataShipRead(
                nullableDouble(row, "armor"),
                dateTime(row, "created_at"),
                nullableLong(row, "crew_capacity"),
                nullableLong(row, "displacement_tons"),
                nullableLong(row, "durability"),
                nullableBoolean(row, "has_lantern"),
                nullableLong(row, "hold_capacity"),
                longValue(row, "id"),
                string(row, "image_url"),
                nullableBoolean(row, "is_active"),
                nullableBoolean(row, "is_seed_overridden"),
                nullableDouble(row, "maneuverability"),
                mortar == null ? null : mortar(mortar),
                requiredString(row, "name"),
                longValue(row, "rate"),
                nullableLong(row, "sail_slots"),
                nullableLong(row, "sailor_minimum"),
                string(row, "seed_key"),
                string(row, "seed_revision"),
                seedStatus(row),
                requiredString(row, "ship_type"),
                string(row, "source"),
                nullableDouble(row, "speed_knots"),
                nullableDouble(row, "speed_min_knots"),
                dateTime(row, "updated_at"),
                assembleOverrides(overrideRows, baseEffects),
                nullableLong(row, "upgrade_slots"),
                layout(mounts),
                mounts.stream().map(MasterDataDtoMapper::mount).toList());
    }

    public MasterDataTaxonomyRead taxonomy(List<Map<String, Object>> classRows,
            List<Map<String, Object>> slotRows, List<Map<String, Object>> ruleRows) {
        List<WeaponClassRead> classes = classRows.stream()
                .map(row -> new WeaponClassRead(requiredString(row, "code"), requiredString(row, "label"),
                        longValue(row, "rank")))
                .toList();
        List<WeaponSlotTypeRead> slots = slotRows.stream()
                .map(row -> new WeaponSlotTypeRead(requiredString(row, "code"), requiredString(row, "label"),
                        longValue(row, "sort_order")))
                .toList();
        List<ShipRateWeaponClassRuleRead> rules = ruleRows.stream()
                .map(row -> new ShipRateWeaponClassRuleRead(longValue(row, "rate"),
                        requiredString(row, "weapon_class")))
                .toList();
        List<StatEffectDefinitionRead> definitions = BuildStatCatalog.ALL.stream().map(definition ->
                new StatEffectDefinitionRead(definition.category(), definition.key(), definition.label(),
                        definition.precision(), "build.stats." + definition.key(), definition.unit(),
                        valueType(definition.key()))).toList();
        return new MasterDataTaxonomyRead(rules, definitions, classes, slots);
    }

    private static List<MasterDataShipUpgradeOverrideRead> assembleOverrides(List<Map<String, Object>> rows,
            Map<Long, Map<String, Double>> baseEffects) {
        Map<Long, OverrideValues> grouped = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            long optionId = longValue(row, "option_id");
            OverrideValues value = grouped.computeIfAbsent(optionId, ignored ->
                    new OverrideValues(optionId, requiredString(row, "option_name"),
                            baseEffects.getOrDefault(optionId, Map.of()), new LinkedHashMap<>()));
            value.overrides().put(requiredString(row, "effect_key"), number(row, "effect_value"));
        }
        return grouped.values().stream().map(value -> {
            Map<String, Double> effective = new LinkedHashMap<>(value.base());
            effective.putAll(value.overrides());
            return new MasterDataShipUpgradeOverrideRead(value.base(), Map.copyOf(effective), value.optionId(),
                    value.optionName(), Map.copyOf(value.overrides()));
        }).toList();
    }

    private static MasterDataShipMount mount(Map<String, Object> row) {
        return new MasterDataShipMount(nullableLong(row, "capacity"), nullableDouble(row, "max_caliber_inches"),
                string(row, "max_weapon_class"), requiredString(row, "slot_type"),
                nullableLong(row, "special_weapon_capacity"));
    }

    private static MasterDataShipMortarModification mortar(Map<String, Object> row) {
        return new MasterDataShipMortarModification(
                longValue(row, "broadside_capacity_delta"),
                longValue(row, "crew_capacity_delta"),
                longValue(row, "durability_delta"),
                nullableDouble(row, "hold_capacity_pct"),
                nullableDouble(row, "maneuverability_delta"),
                number(row, "max_caliber_inches"),
                longValue(row, "mortar_capacity"),
                requiredString(row, "source"),
                nullableDouble(row, "speed_pct"));
    }

    private static String seedStatus(Map<String, Object> row) {
        if (row.get("seed_key") == null) return "custom";
        return Boolean.TRUE.equals(row.get("is_seed_overridden")) ? "overridden" : "managed";
    }

    private static String valueType(String key) {
        return key.endsWith("_enabled") ? "boolean" : "number";
    }

    private static String layout(List<Map<String, Object>> mounts) {
        Map<String, Long> capacities = new LinkedHashMap<>();
        for (Map<String, Object> mount : mounts) {
            capacities.put(requiredString(mount, "slot_type"), longValue(mount, "capacity"));
        }
        long broadside = Math.max(capacities.getOrDefault("weapon_port", 0L),
                capacities.getOrDefault("weapon_starboard", 0L));
        return capacities.getOrDefault("weapon_rear", 0L) + "-" + broadside + "-"
                + capacities.getOrDefault("weapon_front", 0L);
    }

    public MasterDataSeedRestoreSummary seedRestore(long categories, long options,
            long overridesDiscarded, long ships) {
        return new MasterDataSeedRestoreSummary(categories, true, options, overridesDiscarded, ships,
                categories + options + ships);
    }

    private static Boolean nullableBoolean(Map<String, Object> row, String key) {
        Object value = row.get(key);
        return value instanceof Boolean flag ? flag : null;
    }

    private static Double nullableDouble(Map<String, Object> row, String key) {
        Object value = row.get(key);
        return value instanceof Number number ? number.doubleValue() : null;
    }

    private static double number(Map<String, Object> row, String key) {
        Double value = nullableDouble(row, key);
        if (value == null) throw new IllegalStateException("Expected numeric column: " + key);
        return value;
    }

    private record OverrideValues(long optionId, String optionName, Map<String, Double> base,
                                  Map<String, Double> overrides) { }
}
