package eu.royalblackwater.api.builds.repository;

import eu.royalblackwater.api.builds.dto.BuildCatalogOption;
import eu.royalblackwater.api.builds.dto.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import eu.royalblackwater.api.dto.ShipRead;
import eu.royalblackwater.api.dto.WeaponPerformanceRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.ships.mapper.ShipMapper;
import eu.royalblackwater.api.ships.repository.ShipRepository;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class BuildCatalogRepository {
    private final JdbcQueryService jdbc;
    private final ShipRepository ships;
    private final ShipMapper shipMapper;

    public BuildCatalogRepository(JdbcQueryService jdbc, ShipRepository ships, ShipMapper shipMapper) {
        this.jdbc = jdbc;
        this.ships = ships;
        this.shipMapper = shipMapper;
    }

    public List<Map<String, Object>> categories() {
        return jdbc.query("""
                select id, key, label, sort_order
                  from build_item_categories
                 where is_active=true
                 order by sort_order, lower(label), id
                """, Map.of());
    }

    public List<Map<String, Object>> roles() {
        return jdbc.query("""
                select slug, label, description, sort_order, created_at, updated_at
                  from build_roles order by sort_order, lower(label), slug
                """, Map.of());
    }

    public List<BuildCatalogOption> options(Long shipId) {
        List<Map<String, Object>> rows = jdbc.query("""
                select o.id, c.key as category_key, o.name, o.source, o.notes, o.image_url,
                       o.option_kind, wc.code as weapon_class, wc.rank as weapon_class_rank,
                       o.weapon_caliber_inches, o.sort_order, o.created_at, o.updated_at,
                       wp.base_damage, wp.reload_seconds
                  from build_item_options o
                  join build_item_categories c on c.id=o.category_id
                  left join weapon_classes wc on wc.id=o.weapon_class_id
                  left join weapon_performance_profiles wp on wp.option_id=o.id
                 where o.is_active=true and c.is_active=true
                 order by c.sort_order, lower(o.name), o.id
                """, Map.of());
        Map<Long, List<String>> allowed = groupedStrings("""
                select link.option_id, slot.code
                  from build_item_option_slot_types link
                  join weapon_slot_types slot on slot.id=link.slot_type_id
                """, "option_id", "code", Map.of());
        Map<Long, Map<String, Number>> baseEffects = groupedEffects("""
                select option_id, effect_key, effect_value from build_item_effects
                """, Map.of());
        Map<Long, Map<String, Number>> overrides = shipId == null ? Map.of() : groupedEffects("""
                select option_id, effect_key, effect_value
                  from ship_upgrade_effect_overrides where ship_id=:ship_id
                """, Map.of("ship_id", shipId));
        BuildShipSnapshot ship = shipId == null ? null : ship(shipId).orElse(null);
        List<BuildCatalogOption> result = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            long id = number(row.get("id")).longValue();
            Map<String, Number> base = baseEffects.getOrDefault(id, Map.of());
            Map<String, Number> effective = new LinkedHashMap<>(base);
            Map<String, Number> override = overrides.get(id);
            if (override != null) effective.putAll(override);
            List<String> slotTypes = allowed.getOrDefault(id, List.of());
            if (ship != null && "weapon".equals(row.get("category_key"))) {
                slotTypes = slotTypes.stream().filter(slot -> compatible(row, ship, slot)).sorted().toList();
                if (slotTypes.isEmpty()) continue;
            }
            WeaponPerformanceRead performance = row.get("base_damage") == null ? null
                    : new WeaponPerformanceRead(number(row.get("base_damage")).doubleValue(),
                            number(row.get("reload_seconds")).doubleValue());
            result.add(new BuildCatalogOption(id, string(row, "category_key"), string(row, "name"),
                    nullable(row, "source"), nullable(row, "notes"), nullable(row, "image_url"),
                    nullable(row, "option_kind"), nullable(row, "weapon_class"), integer(row, "weapon_class_rank"),
                    decimal(row, "weapon_caliber_inches"), integer(row, "sort_order"),
                    eu.royalblackwater.api.persistence.RowValues.dateTime(row, "created_at"),
                    eu.royalblackwater.api.persistence.RowValues.dateTime(row, "updated_at"),
                    List.copyOf(slotTypes), Map.copyOf(base), Map.copyOf(effective), override != null, performance));
        }
        return List.copyOf(result);
    }

    public Optional<BuildShipSnapshot> ship(long shipId) {
        ShipRead read = ships.findActive(shipId).map(shipMapper::toRead).orElse(null);
        if (read == null) return Optional.empty();
        List<Map<String, Object>> mountRows = jdbc.query("""
                select t.code, m.capacity, m.special_weapon_capacity, wc.rank as max_class_rank,
                       m.max_caliber_inches
                  from ship_weapon_mounts m
                  join weapon_slot_types t on t.id=m.slot_type_id
                  left join weapon_classes wc on wc.id=m.max_weapon_class_id
                 where m.ship_id=:ship_id
                """, Map.of("ship_id", shipId));
        Map<String, BuildShipSnapshot.WeaponMount> mounts = new HashMap<>();
        for (Map<String, Object> row : mountRows) {
            mounts.put(string(row, "code"), new BuildShipSnapshot.WeaponMount(integer(row, "capacity"),
                    integer(row, "special_weapon_capacity"), integer(row, "max_class_rank"),
                    decimal(row, "max_caliber_inches")));
        }
        Map<String, Object> raw = jdbc.optional("""
                select mortar_capacity, max_caliber_inches, broadside_capacity_delta,
                       durability_delta, speed_pct, maneuverability_delta,
                       hold_capacity_pct, crew_capacity_delta
                  from ship_mortar_modifications where ship_id=:ship_id
                """, Map.of("ship_id", shipId)).orElse(null);
        BuildShipSnapshot.MortarModification modification = raw == null ? null
                : new BuildShipSnapshot.MortarModification(integer(raw, "mortar_capacity"),
                        number(raw.get("max_caliber_inches")).doubleValue(),
                        integer(raw, "broadside_capacity_delta"), mortarEffects(raw));
        Map<String, Number> baseStats = Map.ofEntries(
                Map.entry("durability", read.durability()), Map.entry("speed_min_knots", read.speedMinKnots()),
                Map.entry("speed_knots", read.speedKnots()), Map.entry("maneuverability", read.maneuverability()),
                Map.entry("armor", read.armor()), Map.entry("hold_capacity", read.holdCapacity()),
                Map.entry("crew_capacity", read.crewCapacity()), Map.entry("sailor_minimum", read.sailorMinimum()),
                Map.entry("displacement_tons", read.displacementTons()));
        return Optional.of(new BuildShipSnapshot(read, Math.toIntExact(read.upgradeSlots()),
                Math.toIntExact(read.crewCapacity()), Math.toIntExact(read.sailorMinimum()), read.hasLantern(),
                Map.copyOf(mounts), modification, baseStats));
    }

    public Optional<BuildFeatureSnapshot> researchFeature() {
        return feature(null, true);
    }

    public Optional<BuildFeatureSnapshot> feature(Long featureId) {
        return feature(featureId, false);
    }

    private Optional<BuildFeatureSnapshot> feature(Long featureId, boolean activeResearchOnly) {
        String sql = activeResearchOnly
                ? "select id, upgrade_slots_granted from build_features where code='research_upgrade_slot' and is_active=true"
                : "select id, upgrade_slots_granted from build_features where id=:id";
        Map<String, ?> parameters = activeResearchOnly ? Map.of() : Map.of("id", featureId);
        Optional<Map<String, Object>> feature = jdbc.optional(sql, parameters);
        if (feature.isEmpty()) return Optional.empty();
        long id = number(feature.get().get("id")).longValue();
        Map<String, Number> effects = jdbc.query("""
                select effect_key, effect_value from build_feature_effects where feature_id=:id
                """, Map.of("id", id)).stream().collect(LinkedHashMap::new,
                        (map, row) -> map.put(string(row, "effect_key"), normalized(number(row.get("effect_value")))),
                        Map::putAll);
        return Optional.of(new BuildFeatureSnapshot(id, integer(feature.get(), "upgrade_slots_granted"),
                Map.copyOf(effects)));
    }

    private Map<Long, List<String>> groupedStrings(String sql, String idKey, String valueKey, Map<String, ?> params) {
        Map<Long, List<String>> result = new HashMap<>();
        for (Map<String, Object> row : jdbc.query(sql, params)) {
            result.computeIfAbsent(number(row.get(idKey)).longValue(), ignored -> new ArrayList<>())
                    .add(string(row, valueKey));
        }
        return result;
    }

    private Map<Long, Map<String, Number>> groupedEffects(String sql, Map<String, ?> params) {
        Map<Long, Map<String, Number>> result = new HashMap<>();
        for (Map<String, Object> row : jdbc.query(sql, params)) {
            result.computeIfAbsent(number(row.get("option_id")).longValue(), ignored -> new LinkedHashMap<>())
                    .put(string(row, "effect_key"), normalized(number(row.get("effect_value"))));
        }
        return result;
    }

    private static boolean compatible(Map<String, Object> option, BuildShipSnapshot ship, String slot) {
        BuildShipSnapshot.WeaponMount mount = ship.mounts().get(slot);
        if (mount == null || ship.capacity(slot, true) <= 0) return false;
        String kind = nullable(option, "option_kind");
        if ("weapon_mortar".equals(slot)) {
            if (!List.of("mortar", "mortar_launcher").contains(kind)) return false;
            Double caliber = decimal(option, "weapon_caliber_inches");
            Double max = ship.mortarCaliber(true);
            return "mortar_launcher".equals(kind) || caliber == null || max != null && caliber <= max;
        }
        if ("special_weapon".equals(kind)) {
            return List.of("weapon_front", "weapon_rear", "weapon_special").contains(slot)
                    && mount.specialCapacity() > 0;
        }
        if (List.of("mortar", "mortar_launcher").contains(kind)) return false;
        Integer rank = integer(option, "weapon_class_rank");
        return List.of("cannon", "bow_stern").contains(kind) && rank != null
                && mount.maxClassRank() != null && rank <= mount.maxClassRank();
    }

    private static Map<String, Number> mortarEffects(Map<String, Object> row) {
        return Map.of("durability", integer(row, "durability_delta"),
                "speed_pct", number(row.get("speed_pct")),
                "maneuverability", number(row.get("maneuverability_delta")),
                "hold_capacity_pct", number(row.get("hold_capacity_pct")),
                "crew_capacity", integer(row, "crew_capacity_delta"));
    }

    private static Number normalized(Number value) {
        double decimal = value.doubleValue();
        return decimal == Math.rint(decimal) ? value.longValue() : decimal;
    }
    private static Number number(Object value) { return (Number) value; }
    private static String string(Map<String, Object> row, String key) { return String.valueOf(row.get(key)); }
    private static String nullable(Map<String, Object> row, String key) {
        Object value = row.get(key); return value == null ? null : String.valueOf(value);
    }
    private static Integer integer(Map<String, Object> row, String key) {
        Object value = row.get(key); return value instanceof Number number ? number.intValue() : null;
    }
    private static Double decimal(Map<String, Object> row, String key) {
        Object value = row.get(key); return value instanceof Number number ? number.doubleValue() : null;
    }
}
