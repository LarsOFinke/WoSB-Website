package eu.royalblackwater.api.masterdata;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static org.springframework.http.HttpStatus.NOT_FOUND;

import eu.royalblackwater.api.builds.BuildStatCatalog;
import eu.royalblackwater.api.contract.MasterDataCategoryRead;
import eu.royalblackwater.api.contract.MasterDataOptionRead;
import eu.royalblackwater.api.contract.MasterDataOverview;
import eu.royalblackwater.api.contract.MasterDataShipRead;
import eu.royalblackwater.api.contract.MasterDataTaxonomyRead;
import eu.royalblackwater.api.contract.ShipRateWeaponClassRuleRead;
import eu.royalblackwater.api.contract.StatEffectDefinitionRead;
import eu.royalblackwater.api.contract.WeaponClassRead;
import eu.royalblackwater.api.contract.WeaponSlotTypeRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.transport.ContractConversionService;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class MasterDataQueryService {
    private final JdbcQueryService jdbc;
    private final ContractConversionService contracts;

    public MasterDataQueryService(JdbcQueryService jdbc, ContractConversionService contracts) {
        this.jdbc = jdbc;
        this.contracts = contracts;
    }

    @Transactional(readOnly = true)
    public MasterDataOverview overview() {
        return new MasterDataOverview(
                jdbc.count("select count(*) from build_item_categories", Map.of()),
                jdbc.count("""
                        select (select count(*) from build_item_categories where not is_active)
                             + (select count(*) from build_item_options where not is_active)
                             + (select count(*) from ships where not is_active)
                        """, Map.of()),
                jdbc.count("select count(*) from build_item_options", Map.of()),
                jdbc.count("""
                        select (select count(*) from build_item_categories where is_seed_overridden)
                             + (select count(*) from build_item_options where is_seed_overridden)
                             + (select count(*) from ships where is_seed_overridden)
                        """, Map.of()),
                jdbc.count("select count(*) from ships", Map.of()));
    }

    @Transactional(readOnly = true)
    public List<MasterDataCategoryRead> categories() {
        return jdbc.query("select * from build_item_categories order by sort_order,key,id", Map.of()).stream()
                .map(this::category).toList();
    }

    @Transactional(readOnly = true)
    public List<MasterDataOptionRead> options() {
        List<Map<String, Object>> rows = optionRows(null);
        Map<Long, List<String>> slots = groupedStrings("""
                select link.option_id, type.code
                  from build_item_option_slot_types link
                  join weapon_slot_types type on type.id=link.slot_type_id
                 order by link.option_id,type.sort_order,type.code
                """, Map.of());
        Map<Long, Map<String, Double>> effects = groupedEffects(
                "select option_id,effect_key,effect_value from build_item_effects order by option_id,effect_key", Map.of());
        return rows.stream().map(row -> option(row, slots, effects)).toList();
    }

    @Transactional(readOnly = true)
    public List<MasterDataShipRead> ships() {
        return assembleShips(jdbc.query("select * from ships order by rate,name,id", Map.of()));
    }

    @Transactional(readOnly = true)
    public MasterDataCategoryRead category(long id) {
        return category(jdbc.optional("select * from build_item_categories where id=:id", Map.of("id", id))
                .orElseThrow(() -> notFound("Category")));
    }

    @Transactional(readOnly = true)
    public MasterDataOptionRead option(long id) {
        List<Map<String, Object>> rows = optionRows(id);
        if (rows.isEmpty()) {
            throw notFound("Option");
        }
        Map<String, Object> parameters = Map.of("ids", List.of(id));
        Map<Long, List<String>> slots = groupedStrings("""
                select link.option_id, type.code
                  from build_item_option_slot_types link
                  join weapon_slot_types type on type.id=link.slot_type_id
                 where link.option_id in (:ids)
                 order by link.option_id,type.sort_order,type.code
                """, parameters);
        Map<Long, Map<String, Double>> effects = groupedEffects("""
                select option_id,effect_key,effect_value
                  from build_item_effects
                 where option_id in (:ids)
                 order by option_id,effect_key
                """, parameters);
        return option(rows.getFirst(), slots, effects);
    }

    @Transactional(readOnly = true)
    public MasterDataShipRead ship(long id) {
        List<MasterDataShipRead> result = assembleShips(
                jdbc.query("select * from ships where id=:id", Map.of("id", id)));
        if (result.isEmpty()) {
            throw notFound("Ship");
        }
        return result.getFirst();
    }

    @Transactional(readOnly = true)
    public MasterDataTaxonomyRead taxonomy() {
        List<WeaponClassRead> classes = jdbc.query(
                        "select code,label,rank from weapon_classes order by rank,code", Map.of())
                .stream().map(row -> contracts.convert(row, WeaponClassRead.class)).toList();
        List<WeaponSlotTypeRead> slots = jdbc.query(
                        "select code,label,sort_order from weapon_slot_types order by sort_order,code", Map.of())
                .stream().map(row -> contracts.convert(row, WeaponSlotTypeRead.class)).toList();
        List<ShipRateWeaponClassRuleRead> rules = jdbc.query("""
                select rule.rate,wc.code weapon_class
                  from ship_rate_weapon_class_rules rule
                  join weapon_classes wc on wc.id=rule.weapon_class_id
                 order by rule.rate
                """, Map.of()).stream()
                .map(row -> contracts.convert(row, ShipRateWeaponClassRuleRead.class)).toList();
        List<StatEffectDefinitionRead> definitions = BuildStatCatalog.ALL.stream().map(definition ->
                new StatEffectDefinitionRead(definition.category(), definition.key(), definition.label(),
                        definition.precision(), "build.stats." + definition.key(), definition.unit(),
                        valueType(definition.key()))).toList();
        return new MasterDataTaxonomyRead(rules, definitions, classes, slots);
    }

    private List<Map<String, Object>> optionRows(Long id) {
        String predicate = id == null ? "" : " where o.id=:id";
        return jdbc.query("""
                select o.*, c.key category_key, c.label category_label, wc.code weapon_class,
                       wp.base_damage, wp.reload_seconds
                  from build_item_options o
                  join build_item_categories c on c.id=o.category_id
                  left join weapon_classes wc on wc.id=o.weapon_class_id
                  left join weapon_performance_profiles wp on wp.option_id=o.id
                """ + predicate + " order by c.sort_order,o.sort_order,o.name,o.id",
                id == null ? Map.of() : Map.of("id", id));
    }

    private List<MasterDataShipRead> assembleShips(List<Map<String, Object>> rows) {
        if (rows.isEmpty()) {
            return List.of();
        }
        List<Long> ids = rows.stream().map(row -> longValue(row, "id")).toList();
        Map<String, Object> parameters = Map.of("ids", ids);
        Map<Long, List<Map<String, Object>>> mounts = groupedRows("""
                select m.ship_id,type.code slot_type,m.capacity,m.special_weapon_capacity,
                       wc.code max_weapon_class,m.max_caliber_inches
                  from ship_weapon_mounts m
                  join weapon_slot_types type on type.id=m.slot_type_id
                  left join weapon_classes wc on wc.id=m.max_weapon_class_id
                 where m.ship_id in (:ids)
                 order by m.ship_id,type.sort_order,type.code
                """, parameters, "ship_id");
        Map<Long, Map<String, Object>> mortars = indexedRows(
                "select * from ship_mortar_modifications where ship_id in (:ids)", parameters, "ship_id");
        Map<Long, Map<String, Double>> baseEffects = groupedEffects(
                "select option_id,effect_key,effect_value from build_item_effects order by option_id,effect_key", Map.of());
        Map<Long, List<Map<String, Object>>> overrides = groupedRows("""
                select value.ship_id,value.option_id,option.name option_name,value.effect_key,value.effect_value
                  from ship_upgrade_effect_overrides value
                  join build_item_options option on option.id=value.option_id
                 where value.ship_id in (:ids)
                 order by value.ship_id,value.option_id,value.effect_key
                """, parameters, "ship_id");
        return rows.stream().map(row -> ship(row,
                mounts.getOrDefault(longValue(row, "id"), List.of()),
                mortars.get(longValue(row, "id")),
                overrides.getOrDefault(longValue(row, "id"), List.of()),
                baseEffects)).toList();
    }

    private MasterDataCategoryRead category(Map<String, Object> row) {
        Map<String, Object> values = contractValues(row);
        values.put("seed_status", seedStatus(row));
        return contracts.convert(values, MasterDataCategoryRead.class);
    }

    private MasterDataOptionRead option(Map<String, Object> row, Map<Long, List<String>> slots,
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

    private MasterDataShipRead ship(Map<String, Object> row, List<Map<String, Object>> mounts,
            Map<String, Object> mortar, List<Map<String, Object>> overrideRows,
            Map<Long, Map<String, Double>> baseEffects) {
        Map<String, Object> values = contractValues(row);
        values.put("weapon_mounts", mounts.stream().map(MasterDataQueryService::withoutShipId).toList());
        values.put("weapon_layout", layout(mounts));
        values.put("seed_status", seedStatus(row));
        values.put("mortar_modification", mortar == null ? null : withoutShipId(mortar));
        values.put("upgrade_effect_overrides", assembleOverrides(overrideRows, baseEffects));
        return contracts.convert(values, MasterDataShipRead.class);
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

    private Map<Long, List<String>> groupedStrings(String sql, Map<String, ?> parameters) {
        Map<Long, List<String>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : jdbc.query(sql, parameters)) {
            result.computeIfAbsent(longValue(row, "option_id"), ignored -> new ArrayList<>())
                    .add(requiredString(row, "code"));
        }
        return result;
    }

    private Map<Long, Map<String, Double>> groupedEffects(String sql, Map<String, ?> parameters) {
        Map<Long, Map<String, Double>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : jdbc.query(sql, parameters)) {
            result.computeIfAbsent(longValue(row, "option_id"), ignored -> new LinkedHashMap<>())
                    .put(requiredString(row, "effect_key"), ((Number) row.get("effect_value")).doubleValue());
        }
        return result;
    }

    private Map<Long, List<Map<String, Object>>> groupedRows(String sql, Map<String, ?> parameters, String key) {
        Map<Long, List<Map<String, Object>>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : jdbc.query(sql, parameters)) {
            result.computeIfAbsent(longValue(row, key), ignored -> new ArrayList<>()).add(row);
        }
        return result;
    }

    private Map<Long, Map<String, Object>> indexedRows(String sql, Map<String, ?> parameters, String key) {
        Map<Long, Map<String, Object>> result = new LinkedHashMap<>();
        for (Map<String, Object> row : jdbc.query(sql, parameters)) {
            result.put(longValue(row, key), row);
        }
        return result;
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

    private static ResponseStatusException notFound(String subject) {
        return new ResponseStatusException(NOT_FOUND, subject + " not found.");
    }
}
