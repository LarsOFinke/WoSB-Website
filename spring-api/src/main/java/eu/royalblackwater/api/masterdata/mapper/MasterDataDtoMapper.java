package eu.royalblackwater.api.masterdata.mapper;

import eu.royalblackwater.api.builds.model.BuildStatCatalog;
import eu.royalblackwater.api.dto.MasterDataCategoryRead;
import eu.royalblackwater.api.dto.MasterDataOptionRead;
import eu.royalblackwater.api.dto.MasterDataOverview;
import eu.royalblackwater.api.dto.MasterDataShipRead;
import eu.royalblackwater.api.dto.MasterDataSeedRestoreSummary;
import eu.royalblackwater.api.dto.MasterDataTaxonomyRead;
import eu.royalblackwater.api.dto.ShipRateWeaponClassRuleRead;
import eu.royalblackwater.api.dto.StatEffectDefinitionRead;
import eu.royalblackwater.api.dto.WeaponClassRead;
import eu.royalblackwater.api.dto.WeaponSlotTypeRead;
import eu.royalblackwater.api.shared.mapper.ContractConversionService;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;

@Component
public class MasterDataDtoMapper {
    private final ContractConversionService contracts;

    public MasterDataDtoMapper(ContractConversionService contracts) {
        this.contracts = contracts;
    }

    public MasterDataOverview overview(long categoryCount, long optionCount, long shipCount,
            long weaponClassCount, long slotTypeCount) {
        return new MasterDataOverview(categoryCount, optionCount, shipCount, weaponClassCount, slotTypeCount);
    }

    public MasterDataCategoryRead category(Map<String, Object> row) {
        Map<String, Object> values = contractValues(row);
        values.put("seed_status", seedStatus(row));
        return contracts.convert(values, MasterDataCategoryRead.class);
    }

    public MasterDataOptionRead option(Map<String, Object> row, Map<Long, List<String>> slots,
            Map<Long, Map<String, Double>> effects) {
        long id = longValue(row, "id");
        Map<String, Object> values = contractValues(row);
        values.put("allowed_slot_types", slots.getOrDefault(id, List.of()));
        values.put("stat_effects", effects.getOrDefault(id, Map.of()));
        values.put("seed_status", seedStatus(row));
        if (row.get("base_damage") == null) {
            values.put("weapon_performance", null);
        } else {
            Map<String, Object> performance = new LinkedHashMap<>();
            performance.put("base_damage", row.get("base_damage"));
            performance.put("reload_seconds", row.get("reload_seconds"));
            values.put("weapon_performance", performance);
        }
        return contracts.convert(values, MasterDataOptionRead.class);
    }

    public MasterDataShipRead ship(Map<String, Object> row, List<Map<String, Object>> mounts,
            Map<String, Object> mortar, List<Map<String, Object>> overrideRows,
            Map<Long, Map<String, Double>> baseEffects) {
        Map<String, Object> values = contractValues(row);
        values.put("weapon_mounts", mounts.stream().map(MasterDataDtoMapper::withoutShipId).toList());
        values.put("weapon_layout", layout(mounts));
        values.put("seed_status", seedStatus(row));
        values.put("mortar_modification", mortar == null ? null : withoutShipId(mortar));
        values.put("upgrade_effect_overrides", assembleOverrides(overrideRows, baseEffects));
        return contracts.convert(values, MasterDataShipRead.class);
    }

    public MasterDataTaxonomyRead taxonomy(List<Map<String, Object>> classRows,
            List<Map<String, Object>> slotRows, List<Map<String, Object>> ruleRows) {
        List<WeaponClassRead> classes = classRows.stream()
                .map(row -> contracts.convert(row, WeaponClassRead.class)).toList();
        List<WeaponSlotTypeRead> slots = slotRows.stream()
                .map(row -> contracts.convert(row, WeaponSlotTypeRead.class)).toList();
        List<ShipRateWeaponClassRuleRead> rules = ruleRows.stream()
                .map(row -> contracts.convert(row, ShipRateWeaponClassRuleRead.class)).toList();
        List<StatEffectDefinitionRead> definitions = BuildStatCatalog.ALL.stream().map(definition ->
                new StatEffectDefinitionRead(definition.category(), definition.key(), definition.label(),
                        definition.precision(), "build.stats." + definition.key(), definition.unit(),
                        valueType(definition.key()))).toList();
        return new MasterDataTaxonomyRead(rules, definitions, classes, slots);
    }

    private static List<Map<String, Object>> assembleOverrides(List<Map<String, Object>> rows,
            Map<Long, Map<String, Double>> baseEffects) {
        Map<Long, Map<String, Object>> grouped = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            long optionId = longValue(row, "option_id");
            Map<String, Object> value = grouped.computeIfAbsent(optionId, ignored -> {
                Map<String, Object> created = new LinkedHashMap<>();
                created.put("option_id", optionId);
                created.put("option_name", requiredString(row, "option_name"));
                created.put("base_stat_effects", baseEffects.getOrDefault(optionId, Map.of()));
                created.put("stat_effects", new LinkedHashMap<String, Double>());
                return created;
            });
            @SuppressWarnings("unchecked")
            Map<String, Double> effects = (Map<String, Double>) value.get("stat_effects");
            effects.put(requiredString(row, "effect_key"), ((Number) row.get("effect_value")).doubleValue());
        }
        for (Map<String, Object> value : grouped.values()) {
            @SuppressWarnings("unchecked")
            Map<String, Double> base = (Map<String, Double>) value.get("base_stat_effects");
            @SuppressWarnings("unchecked")
            Map<String, Double> overrides = (Map<String, Double>) value.get("stat_effects");
            Map<String, Double> effective = new LinkedHashMap<>(base);
            effective.putAll(overrides);
            value.put("effective_stat_effects", effective);
        }
        return List.copyOf(grouped.values());
    }

    private static String seedStatus(Map<String, Object> row) {
        if (row.get("seed_key") == null) {
            return "custom";
        }
        return Boolean.TRUE.equals(row.get("is_seed_overridden")) ? "overridden" : "managed";
    }

    private static Map<String, Object> contractValues(Map<String, Object> row) {
        Map<String, Object> values = new LinkedHashMap<>(row);
        values.remove("seed_checksum");
        values.remove("weapon_class_id");
        values.remove("base_damage");
        values.remove("reload_seconds");
        return values;
    }

    private static Map<String, Object> withoutShipId(Map<String, Object> row) {
        Map<String, Object> values = new LinkedHashMap<>(row);
        values.remove("ship_id");
        return values;
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

}
