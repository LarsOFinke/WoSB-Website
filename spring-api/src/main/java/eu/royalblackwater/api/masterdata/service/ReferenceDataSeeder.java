package eu.royalblackwater.api.masterdata.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.masterdata.repository.SeedCatalog;
import eu.royalblackwater.api.masterdata.repository.MasterDataRepository;
import eu.royalblackwater.api.masterdata.repository.queries.ReferenceDataQueries;
import eu.royalblackwater.api.persistence.SqlParameters;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.databind.ObjectMapper;

import static eu.royalblackwater.api.persistence.RowValues.longValue;

@Service
public class ReferenceDataSeeder {
    static final String REVISION = "spring-catalog-v1";
    private final SeedCatalog catalog;
    private final MasterDataRepository repository;
    private final ObjectMapper json;
    private final Clock clock;

    public ReferenceDataSeeder(SeedCatalog catalog, MasterDataRepository repository, ObjectMapper json, Clock clock) {
        this.catalog = catalog;
        this.repository = repository;
        this.json = json;
        this.clock = clock;
    }

    @Order(10)
    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void synchronizeAtStartup() { synchronize(false); }

    @Transactional
    public SeedResult synchronize(boolean discardOverrides) {
        seedSystemData();
        seedTaxonomy();
        long categories = seedCategories(discardOverrides);
        long options = seedOptions(discardOverrides);
        long ships = seedShips(discardOverrides);
        seedBuildRules();
        seedBuildRoles();
        return new SeedResult(categories, options, ships, discardOverrides ? categories + options + ships : 0);
    }

    private void seedSystemData() {
        LocalDateTime now = UtcDateTimes.now(clock);
        Map<String, Object> roles = catalog.systemRoles();
        for (Map<String, Object> item : SeedCatalog.listOfMaps(roles.get("site_roles"))) {
            repository.update(ReferenceDataQueries.SEED_SYSTEM_DATA_INSERT_01, Map.of("code", text(item,"code"), "label", text(item,"label"),
                    "rank", integer(item,"rank",0), "staff", flag(item,"is_staff",false),
                    "system", flag(item,"can_manage_system",false), "now", now));
        }
        for (Map<String, Object> item : SeedCatalog.listOfMaps(roles.get("fleet_roles"))) {
            repository.update(ReferenceDataQueries.SEED_SYSTEM_DATA_INSERT_02, Map.of("code", text(item,"code"), "label", text(item,"label"),
                    "rank", integer(item,"rank",0), "leadership", flag(item,"is_leadership",false),
                    "manageFleet", flag(item,"can_manage_fleet",false),
                    "manageMembers", flag(item,"can_manage_members",false),
                    "system", flag(item,"is_system",true), "active", flag(item,"is_active",true), "now", now));
        }
        for (Map<String, Object> item : SeedCatalog.listOfMaps(roles.get("squad_roles"))) {
            repository.update(ReferenceDataQueries.SEED_SYSTEM_DATA_INSERT_03, Map.of("code", text(item,"code"), "label", text(item,"label"),
                    "rank", integer(item,"rank",0), "roster", flag(item,"can_manage_roster",false),
                    "events", flag(item,"can_manage_events",false), "now", now));
        }
        for (Map<String, Object> item : catalog.systemFleets()) {
            repository.update(ReferenceDataQueries.SEED_SYSTEM_DATA_INSERT_04, SqlParameters.ofNullable("name", text(item,"name"), "slug", text(item,"slug"),
                    "focus", text(item,"focus"), "description", nullable(item,"description"),
                    "orders", nullable(item,"standing_orders"), "sort", integer(item,"sort_order",0), "now", now));
        }
    }

    private void seedTaxonomy() {
        Map<String, Object> definitions = catalog.definitions();
        for (Map<String, Object> item : SeedCatalog.listOfMaps(definitions.get("weapon_classes"))) {
            repository.update(ReferenceDataQueries.SEED_TAXONOMY_INSERT_01, Map.of("code", text(item,"code"), "label", text(item,"label"), "rank", integer(item,"rank",0)));
        }
        for (Map<String, Object> item : SeedCatalog.listOfMaps(definitions.get("weapon_slot_types"))) {
            repository.update(ReferenceDataQueries.SEED_TAXONOMY_INSERT_02, Map.of("code", text(item,"code"), "label", text(item,"label"), "sort", integer(item,"sort_order",0)));
        }
    }

    private long seedCategories(boolean discard) {
        long changed = 0;
        for (Map<String, Object> item : catalog.categories()) {
            String key = text(item,"key");
            String seedKey = "category:" + key;
            Map<String, Object> values = Map.of("key", key, "label", text(item,"label"),
                    "sort", integer(item,"sort_order",0), "seed", seedKey, "revision", REVISION,
                    "checksum", checksum(item), "now", UtcDateTimes.now(clock), "discard", discard);
            changed += repository.update(ReferenceDataQueries.SEED_CATEGORIES_INSERT_01, values);
        }
        return changed;
    }

    private long seedOptions(boolean discard) {
        long changed = 0;
        int sort = 0;
        for (Map<String, Object> item : catalog.options()) {
            long categoryId = requiredId("build_item_categories", "key", text(item,"category"));
            String seedKey = "option:" + text(item,"category") + ":" + text(item,"seed_id");
            Long weaponClassId = optionalId("weapon_classes", "code", nullable(item,"weapon_class"));
            Map<String, Object> params = SqlParameters.ofNullable("category",categoryId,"name",text(item,"name"),
                    "source",nullable(item,"source"),"notes",nullable(item,"notes"),"image",nullable(item,"image_url"),
                    "kind",nullable(item,"option_kind"),"weaponClass",weaponClassId,
                    "caliber",number(item,"weapon_caliber_inches"),"sort",++sort,"seed",seedKey,
                    "revision",REVISION,"checksum",checksum(item),"now",UtcDateTimes.now(clock),"discard",discard);
            repository.update(ReferenceDataQueries.SEED_OPTIONS_INSERT_01, params);
            long optionId = repository.optional(ReferenceDataQueries.SEED_OPTIONS_SELECT_01,
                    Map.of("category",categoryId,"name",text(item,"name"))).map(row -> longValue(row,"id"))
                    .orElseThrow(() -> new IllegalStateException("Seeded option was not persisted."));
            if (discard || !overridden("build_item_options", optionId)) replaceOptionChildren(optionId, item);
            changed++;
        }
        return changed;
    }

    private void replaceOptionChildren(long optionId, Map<String, Object> item) {
        repository.update(ReferenceDataQueries.REPLACE_OPTION_CHILDREN_DELETE_01, Map.of("id",optionId));
        for (Map.Entry<String,Object> effect : map(item.get("stat_effects")).entrySet()) {
            repository.update(ReferenceDataQueries.REPLACE_OPTION_CHILDREN_INSERT_01, Map.of("id",optionId,"key",effect.getKey(),
                    "value",((Number)effect.getValue()).doubleValue(),"now",UtcDateTimes.now(clock)));
        }
        repository.update(ReferenceDataQueries.REPLACE_OPTION_CHILDREN_DELETE_02, Map.of("id",optionId));
        for (String code : strings(item.get("allowed_slot_types"))) {
            Long slotId = optionalId("weapon_slot_types", "code", code);
            if (slotId != null) repository.update(ReferenceDataQueries.REPLACE_OPTION_CHILDREN_INSERT_02,
                    Map.of("id",optionId,"slot",slotId));
        }
        repository.update(ReferenceDataQueries.REPLACE_OPTION_CHILDREN_DELETE_03, Map.of("id",optionId));
        Map<String,Object> performance = map(item.get("weapon_performance"));
        if (!performance.isEmpty()) repository.update(ReferenceDataQueries.REPLACE_OPTION_CHILDREN_INSERT_03, Map.of("id",optionId,"damage",number(performance,"base_damage"),
                        "reload",number(performance,"reload_seconds")));
    }

    private long seedShips(boolean discard) {
        long changed = 0;
        for (Map<String, Object> item : catalog.ships()) {
            String seedKey = "ship:" + text(item,"seed_id");
            Map<String, Object> params = SqlParameters.ofNullable("name",text(item,"name"),"rate",integer(item,"rate",7),
                    "type",text(item,"ship_type"),"durability",integer(item,"durability",0),
                    "speedMin",number(item,"speed_min_knots"),"speed",number(item,"speed_knots"),
                    "maneuver",number(item,"maneuverability"),"armor",number(item,"armor"),
                    "hold",integer(item,"hold_capacity",0),"crew",integer(item,"crew_capacity",0),
                    "sailors",integer(item,"sailor_minimum",0),"displacement",integer(item,"displacement_tons",0),
                    "source",nullable(item,"source"),"image",nullable(item,"image_url"),"sails",integer(item,"sail_slots",0),
                    "upgrades",integer(item,"upgrade_slots",0),"lantern",flag(item,"has_lantern",false),
                    "active",flag(item,"is_active",true),"seed",seedKey,"revision",REVISION,"checksum",checksum(item),
                    "now",UtcDateTimes.now(clock),"discard",discard);
            repository.update(ReferenceDataQueries.SEED_SHIPS_INSERT_01, params);
            long shipId = requiredId("ships", "name", text(item,"name"));
            if (discard || !overridden("ships", shipId)) replaceShipChildren(shipId, item);
            changed++;
        }
        return changed;
    }

    private void replaceShipChildren(long shipId, Map<String, Object> item) {
        repository.update(ReferenceDataQueries.REPLACE_SHIP_CHILDREN_DELETE_01, Map.of("id",shipId));
        for (Map<String,Object> mount : SeedCatalog.listOfMaps(item.get("weapon_mounts"))) {
            Long slot = optionalId("weapon_slot_types", "code", text(mount,"slot_type"));
            Long weaponClass = optionalId("weapon_classes", "code", nullable(mount,"max_weapon_class"));
            repository.update(ReferenceDataQueries.REPLACE_SHIP_CHILDREN_INSERT_01, SqlParameters.ofNullable("ship",shipId,"slot",slot,"capacity",integer(mount,"capacity",0),
                            "special",integer(mount,"special_weapon_capacity",0),"class",weaponClass,
                            "caliber",number(mount,"max_caliber_inches")));
        }
        repository.update(ReferenceDataQueries.REPLACE_SHIP_CHILDREN_DELETE_02, Map.of("id",shipId));
        Map<String,Object> mortar = map(item.get("mortar_modification"));
        if (!mortar.isEmpty()) repository.update(ReferenceDataQueries.REPLACE_SHIP_CHILDREN_INSERT_02, Map.of("ship",shipId,"capacity",integer(mortar,"mortar_capacity",1),
                        "caliber",number(mortar,"max_caliber_inches"),"broadside",integer(mortar,"broadside_capacity_delta",0),
                        "durability",integer(mortar,"durability_delta",0),"speed",number(mortar,"speed_pct"),
                        "maneuver",number(mortar,"maneuverability_delta"),"hold",number(mortar,"hold_capacity_pct"),
                        "crew",integer(mortar,"crew_capacity_delta",0),"source",text(mortar,"source")));
        repository.update(ReferenceDataQueries.REPLACE_SHIP_CHILDREN_DELETE_03, Map.of("id", shipId));
        for (Map<String, Object> override : SeedCatalog.listOfMaps(item.get("upgrade_effect_overrides"))) {
            String seedId = text(override, "upgrade_seed_id");
            long optionId = requiredOptionId("option:upgrade:" + seedId);
            for (Map.Entry<String, Object> effect : map(override.get("stat_effects")).entrySet()) {
                repository.update(ReferenceDataQueries.REPLACE_SHIP_CHILDREN_INSERT_03,
                        Map.of("ship", shipId, "option", optionId, "key", effect.getKey(),
                                "value", ((Number) effect.getValue()).doubleValue(), "now", UtcDateTimes.now(clock)));
            }
        }
    }

    private void seedBuildRules() {
        Map<String,Object> rules = catalog.buildRules();
        for (Map<String,Object> item : SeedCatalog.listOfMaps(rules.get("build_features"))) {
            repository.update(ReferenceDataQueries.SEED_BUILD_RULES_INSERT_01, Map.of("code",text(item,"code"),"label",text(item,"label"),
                            "slots",integer(item,"upgrade_slots_granted",0)));
            long id = requiredId("build_features", "code", text(item,"code"));
            repository.update(ReferenceDataQueries.SEED_BUILD_RULES_DELETE_01, Map.of("id",id));
            for (Map.Entry<String,Object> effect : map(item.get("stat_effects")).entrySet()) {
                repository.update(ReferenceDataQueries.SEED_BUILD_RULES_INSERT_02,
                        Map.of("id",id,"key",effect.getKey(),"value",((Number)effect.getValue()).doubleValue()));
            }
        }
        repository.update(ReferenceDataQueries.SEED_BUILD_RULES_DELETE_02, Map.of());
        for (Map<String,Object> item : SeedCatalog.listOfMaps(rules.get("ship_rate_weapon_classes"))) {
            Long weaponClass = optionalId("weapon_classes", "code", text(item,"weapon_class"));
            repository.update(ReferenceDataQueries.SEED_BUILD_RULES_INSERT_03,
                    Map.of("rate",integer(item,"rate",7),"class",weaponClass));
        }
    }

    private void seedBuildRoles() {
        List<Map<String,Object>> roles = List.of(
                Map.of("slug","balanced","label","Balanced","description","General-purpose build","sort",10),
                Map.of("slug","boarding","label","Boarding","description","Boarding and crew pressure","sort",20),
                Map.of("slug","gunnery","label","Gunnery","description","Weapon damage and reload","sort",30),
                Map.of("slug","defensive","label","Defensive","description","Durability and survivability","sort",40));
        for (Map<String,Object> role : roles) repository.update(ReferenceDataQueries.SEED_BUILD_ROLES_INSERT_01, Map.of("slug",role.get("slug"),"label",role.get("label"),"description",role.get("description"),
                        "sort",role.get("sort"),"now",UtcDateTimes.now(clock)));
    }

    private boolean overridden(String table, long id) {
        if (!List.of("build_item_options","ships").contains(table)) throw new IllegalArgumentException("Unsupported table");
        return repository.count(ReferenceDataQueries.OVERRIDDEN_SELECT_01 + table + ReferenceDataQueries.OVERRIDDEN_WHERE_01, Map.of("id",id)) > 0;
    }

    private long requiredId(String table, String column, String value) {
        if (!List.of("build_item_categories","ships","build_features").contains(table)
                || !List.of("key","name","code").contains(column)) throw new IllegalArgumentException("Unsupported lookup");
        return repository.optional(ReferenceDataQueries.REQUIRED_ID_SELECT_01 + table + ReferenceDataQueries.REQUIRED_ID_WHERE_01 + column + "=:value", Map.of("value",value))
                .map(row -> longValue(row,"id")).orElseThrow(() -> new IllegalStateException("Required seed dependency is missing."));
    }

    private long requiredOptionId(String seedKey) {
        return repository.optional(ReferenceDataQueries.SEED_OPTIONS_SELECT_BY_SEED_KEY_01,
                        Map.of("seed", seedKey))
                .map(row -> longValue(row, "id"))
                .orElseThrow(() -> new IllegalStateException("Required upgrade seed dependency is missing: " + seedKey));
    }

    private Long optionalId(String table, String column, String value) {
        if (value == null || value.isBlank()) return null;
        if (!List.of("weapon_classes","weapon_slot_types").contains(table) || !List.of("code").contains(column)) {
            throw new IllegalArgumentException("Unsupported lookup");
        }
        return repository.optional(ReferenceDataQueries.REQUIRED_ID_SELECT_01 + table + ReferenceDataQueries.REQUIRED_ID_WHERE_01 + column + "=:value", Map.of("value",value))
                .map(row -> longValue(row,"id")).orElse(null);
    }

    private String checksum(Map<String,Object> item) {
        try {
            byte[] bytes = json.writeValueAsBytes(new java.util.TreeMap<>(item));
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (Exception exception) {
            throw new IllegalStateException("Could not checksum seed data", exception);
        }
    }
    static String text(Map<String,Object> map,String key) { return String.valueOf(map.get(key)); }
    static String nullable(Map<String,Object> map,String key) { Object value=map.get(key); return value==null?null:String.valueOf(value); }
    static int integer(Map<String,Object> map,String key,int fallback) { Object v=map.get(key); return v instanceof Number n?n.intValue():fallback; }
    static Double number(Map<String,Object> map,String key) { Object v=map.get(key); return v instanceof Number n?n.doubleValue():null; }
    static boolean flag(Map<String,Object> map,String key,boolean fallback) { Object v=map.get(key); return v instanceof Boolean b?b:fallback; }
    static Map<String,Object> map(Object value) {
        if (!(value instanceof Map<?,?> raw)) return Map.of();
        Map<String,Object> result=new LinkedHashMap<>(); raw.forEach((k,v)->result.put(String.valueOf(k),v)); return result;
    }
    static List<String> strings(Object value) { return value instanceof List<?> list?list.stream().map(String::valueOf).toList():List.of(); }
    public record SeedResult(long categories,long options,long ships,long overridesDiscarded) { }
}
