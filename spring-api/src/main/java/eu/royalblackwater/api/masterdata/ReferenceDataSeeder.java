package eu.royalblackwater.api.masterdata;

import static eu.royalblackwater.api.persistence.RowValues.longValue;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.context.event.EventListener;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Service
public class ReferenceDataSeeder {
    static final String REVISION = "spring-catalog-v1";
    private final SeedCatalog catalog;
    private final JdbcQueryService jdbc;
    private final ObjectMapper json;
    private final Clock clock;

    public ReferenceDataSeeder(SeedCatalog catalog, JdbcQueryService jdbc, ObjectMapper json, Clock clock) {
        this.catalog = catalog;
        this.jdbc = jdbc;
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
        LocalDateTime now = now();
        Map<String, Object> roles = catalog.systemRoles();
        for (Map<String, Object> item : SeedCatalog.listOfMaps(roles.get("site_roles"))) {
            jdbc.update("""
                    insert into site_roles(code,label,rank,is_staff,can_manage_system,created_at)
                    values(:code,:label,:rank,:staff,:system,:now)
                    on conflict(code) do update set label=excluded.label,rank=excluded.rank,
                        is_staff=excluded.is_staff,can_manage_system=excluded.can_manage_system
                    """, Map.of("code", text(item,"code"), "label", text(item,"label"),
                    "rank", integer(item,"rank",0), "staff", flag(item,"is_staff",false),
                    "system", flag(item,"can_manage_system",false), "now", now));
        }
        for (Map<String, Object> item : SeedCatalog.listOfMaps(roles.get("fleet_roles"))) {
            jdbc.update("""
                    insert into fleet_roles(code,label,rank,is_leadership,can_manage_fleet,can_manage_members,
                        is_system,is_active,created_at,updated_at)
                    values(:code,:label,:rank,:leadership,:manageFleet,:manageMembers,:system,:active,:now,:now)
                    on conflict(code) do update set label=excluded.label,rank=excluded.rank,
                        is_leadership=excluded.is_leadership,can_manage_fleet=excluded.can_manage_fleet,
                        can_manage_members=excluded.can_manage_members,is_system=excluded.is_system,
                        is_active=excluded.is_active,updated_at=excluded.updated_at
                    """, Map.of("code", text(item,"code"), "label", text(item,"label"),
                    "rank", integer(item,"rank",0), "leadership", flag(item,"is_leadership",false),
                    "manageFleet", flag(item,"can_manage_fleet",false),
                    "manageMembers", flag(item,"can_manage_members",false),
                    "system", flag(item,"is_system",true), "active", flag(item,"is_active",true), "now", now));
        }
        for (Map<String, Object> item : SeedCatalog.listOfMaps(roles.get("squad_roles"))) {
            jdbc.update("""
                    insert into squad_roles(code,label,rank,can_manage_roster,can_manage_events,created_at)
                    values(:code,:label,:rank,:roster,:events,:now)
                    on conflict(code) do update set label=excluded.label,rank=excluded.rank,
                        can_manage_roster=excluded.can_manage_roster,can_manage_events=excluded.can_manage_events
                    """, Map.of("code", text(item,"code"), "label", text(item,"label"),
                    "rank", integer(item,"rank",0), "roster", flag(item,"can_manage_roster",false),
                    "events", flag(item,"can_manage_events",false), "now", now));
        }
        for (Map<String, Object> item : catalog.systemFleets()) {
            jdbc.update("""
                    insert into fleets(name,slug,focus,description,standing_orders,sort_order,is_active,created_at,updated_at)
                    values(:name,:slug,:focus,:description,:orders,:sort,true,:now,:now)
                    on conflict(slug) do update set name=excluded.name,focus=excluded.focus,
                        description=excluded.description,standing_orders=excluded.standing_orders,
                        sort_order=excluded.sort_order,is_active=true,updated_at=excluded.updated_at
                    """, SqlParameters.ofNullable("name", text(item,"name"), "slug", text(item,"slug"),
                    "focus", text(item,"focus"), "description", nullable(item,"description"),
                    "orders", nullable(item,"standing_orders"), "sort", integer(item,"sort_order",0), "now", now));
        }
    }

    private void seedTaxonomy() {
        Map<String, Object> definitions = catalog.definitions();
        for (Map<String, Object> item : SeedCatalog.listOfMaps(definitions.get("weapon_classes"))) {
            jdbc.update("""
                    insert into weapon_classes(code,label,rank) values(:code,:label,:rank)
                    on conflict(code) do update set label=excluded.label, rank=excluded.rank
                    """, Map.of("code", text(item,"code"), "label", text(item,"label"), "rank", integer(item,"rank",0)));
        }
        for (Map<String, Object> item : SeedCatalog.listOfMaps(definitions.get("weapon_slot_types"))) {
            jdbc.update("""
                    insert into weapon_slot_types(code,label,sort_order) values(:code,:label,:sort)
                    on conflict(code) do update set label=excluded.label, sort_order=excluded.sort_order
                    """, Map.of("code", text(item,"code"), "label", text(item,"label"), "sort", integer(item,"sort_order",0)));
        }
    }

    private long seedCategories(boolean discard) {
        long changed = 0;
        for (Map<String, Object> item : catalog.categories()) {
            String key = text(item,"key");
            String seedKey = "category:" + key;
            Map<String, Object> values = Map.of("key", key, "label", text(item,"label"),
                    "sort", integer(item,"sort_order",0), "seed", seedKey, "revision", REVISION,
                    "checksum", checksum(item), "now", now(), "discard", discard);
            changed += jdbc.update("""
                    insert into build_item_categories(key,label,sort_order,is_active,seed_key,seed_revision,
                        seed_checksum,is_seed_overridden,created_at,updated_at)
                    values(:key,:label,:sort,true,:seed,:revision,:checksum,false,:now,:now)
                    on conflict(key) do update set label=excluded.label, sort_order=excluded.sort_order,
                        is_active=true, seed_key=excluded.seed_key, seed_revision=excluded.seed_revision,
                        seed_checksum=excluded.seed_checksum, is_seed_overridden=false, updated_at=excluded.updated_at
                    where :discard or build_item_categories.is_seed_overridden=false
                    """, values);
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
                    "revision",REVISION,"checksum",checksum(item),"now",now(),"discard",discard);
            jdbc.update("""
                    insert into build_item_options(category_id,name,source,notes,image_url,option_kind,weapon_class_id,
                        weapon_caliber_inches,sort_order,is_active,seed_key,seed_revision,seed_checksum,
                        is_seed_overridden,created_at,updated_at)
                    values(:category,:name,:source,:notes,:image,:kind,:weaponClass,:caliber,:sort,true,:seed,
                        :revision,:checksum,false,:now,:now)
                    on conflict(category_id,name) do update set source=excluded.source,notes=excluded.notes,
                        image_url=excluded.image_url,option_kind=excluded.option_kind,weapon_class_id=excluded.weapon_class_id,
                        weapon_caliber_inches=excluded.weapon_caliber_inches,sort_order=excluded.sort_order,is_active=true,
                        seed_key=excluded.seed_key,seed_revision=excluded.seed_revision,seed_checksum=excluded.seed_checksum,
                        is_seed_overridden=false,updated_at=excluded.updated_at
                    where :discard or build_item_options.is_seed_overridden=false
                    """, params);
            long optionId = jdbc.optional("select id from build_item_options where category_id=:category and name=:name",
                    Map.of("category",categoryId,"name",text(item,"name"))).map(row -> longValue(row,"id"))
                    .orElseThrow(() -> new IllegalStateException("Seeded option was not persisted."));
            if (discard || !overridden("build_item_options", optionId)) replaceOptionChildren(optionId, item);
            changed++;
        }
        return changed;
    }

    private void replaceOptionChildren(long optionId, Map<String, Object> item) {
        jdbc.update("delete from build_item_effects where option_id=:id", Map.of("id",optionId));
        for (Map.Entry<String,Object> effect : map(item.get("stat_effects")).entrySet()) {
            jdbc.update("""
                    insert into build_item_effects(option_id,effect_key,effect_value,created_at,updated_at)
                    values(:id,:key,:value,:now,:now)
                    """, Map.of("id",optionId,"key",effect.getKey(),
                    "value",((Number)effect.getValue()).doubleValue(),"now",now()));
        }
        jdbc.update("delete from build_item_option_slot_types where option_id=:id", Map.of("id",optionId));
        for (String code : strings(item.get("allowed_slot_types"))) {
            Long slotId = optionalId("weapon_slot_types", "code", code);
            if (slotId != null) jdbc.update("insert into build_item_option_slot_types(option_id,slot_type_id) values(:id,:slot)",
                    Map.of("id",optionId,"slot",slotId));
        }
        jdbc.update("delete from weapon_performance_profiles where option_id=:id", Map.of("id",optionId));
        Map<String,Object> performance = map(item.get("weapon_performance"));
        if (!performance.isEmpty()) jdbc.update("""
                insert into weapon_performance_profiles(option_id,base_damage,reload_seconds)
                values(:id,:damage,:reload)
                """, Map.of("id",optionId,"damage",number(performance,"base_damage"),
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
                    "now",now(),"discard",discard);
            jdbc.update("""
                    insert into ships(name,rate,ship_type,durability,speed_min_knots,speed_knots,maneuverability,armor,
                        hold_capacity,crew_capacity,sailor_minimum,displacement_tons,source,image_url,sail_slots,
                        upgrade_slots,has_lantern,is_active,seed_key,seed_revision,seed_checksum,is_seed_overridden,
                        created_at,updated_at)
                    values(:name,:rate,:type,:durability,:speedMin,:speed,:maneuver,:armor,:hold,:crew,:sailors,
                        :displacement,:source,:image,:sails,:upgrades,:lantern,:active,:seed,:revision,:checksum,false,:now,:now)
                    on conflict(name) do update set rate=excluded.rate,ship_type=excluded.ship_type,durability=excluded.durability,
                        speed_min_knots=excluded.speed_min_knots,speed_knots=excluded.speed_knots,
                        maneuverability=excluded.maneuverability,armor=excluded.armor,hold_capacity=excluded.hold_capacity,
                        crew_capacity=excluded.crew_capacity,sailor_minimum=excluded.sailor_minimum,
                        displacement_tons=excluded.displacement_tons,source=excluded.source,image_url=excluded.image_url,
                        sail_slots=excluded.sail_slots,upgrade_slots=excluded.upgrade_slots,has_lantern=excluded.has_lantern,
                        is_active=excluded.is_active,seed_key=excluded.seed_key,seed_revision=excluded.seed_revision,
                        seed_checksum=excluded.seed_checksum,is_seed_overridden=false,updated_at=excluded.updated_at
                    where :discard or ships.is_seed_overridden=false
                    """, params);
            long shipId = requiredId("ships", "name", text(item,"name"));
            if (discard || !overridden("ships", shipId)) replaceShipChildren(shipId, item);
            changed++;
        }
        return changed;
    }

    private void replaceShipChildren(long shipId, Map<String, Object> item) {
        jdbc.update("delete from ship_weapon_mounts where ship_id=:id", Map.of("id",shipId));
        for (Map<String,Object> mount : SeedCatalog.listOfMaps(item.get("weapon_mounts"))) {
            Long slot = optionalId("weapon_slot_types", "code", text(mount,"slot_type"));
            Long weaponClass = optionalId("weapon_classes", "code", nullable(mount,"max_weapon_class"));
            jdbc.update("""
                    insert into ship_weapon_mounts(ship_id,slot_type_id,capacity,special_weapon_capacity,
                        max_weapon_class_id,max_caliber_inches)
                    values(:ship,:slot,:capacity,:special,:class,:caliber)
                    """, SqlParameters.ofNullable("ship",shipId,"slot",slot,"capacity",integer(mount,"capacity",0),
                            "special",integer(mount,"special_weapon_capacity",0),"class",weaponClass,
                            "caliber",number(mount,"max_caliber_inches")));
        }
        jdbc.update("delete from ship_mortar_modifications where ship_id=:id", Map.of("id",shipId));
        Map<String,Object> mortar = map(item.get("mortar_modification"));
        if (!mortar.isEmpty()) jdbc.update("""
                insert into ship_mortar_modifications(ship_id,mortar_capacity,max_caliber_inches,
                    broadside_capacity_delta,durability_delta,speed_pct,maneuverability_delta,hold_capacity_pct,
                    crew_capacity_delta,source)
                values(:ship,:capacity,:caliber,:broadside,:durability,:speed,:maneuver,:hold,:crew,:source)
                """, Map.of("ship",shipId,"capacity",integer(mortar,"mortar_capacity",1),
                        "caliber",number(mortar,"max_caliber_inches"),"broadside",integer(mortar,"broadside_capacity_delta",0),
                        "durability",integer(mortar,"durability_delta",0),"speed",number(mortar,"speed_pct"),
                        "maneuver",number(mortar,"maneuverability_delta"),"hold",number(mortar,"hold_capacity_pct"),
                        "crew",integer(mortar,"crew_capacity_delta",0),"source",text(mortar,"source")));
    }

    private void seedBuildRules() {
        Map<String,Object> rules = catalog.buildRules();
        for (Map<String,Object> item : SeedCatalog.listOfMaps(rules.get("build_features"))) {
            jdbc.update("""
                    insert into build_features(code,label,upgrade_slots_granted,is_active)
                    values(:code,:label,:slots,true) on conflict(code) do update set label=excluded.label,
                    upgrade_slots_granted=excluded.upgrade_slots_granted,is_active=true
                    """, Map.of("code",text(item,"code"),"label",text(item,"label"),
                            "slots",integer(item,"upgrade_slots_granted",0)));
            long id = requiredId("build_features", "code", text(item,"code"));
            jdbc.update("delete from build_feature_effects where feature_id=:id", Map.of("id",id));
            for (Map.Entry<String,Object> effect : map(item.get("stat_effects")).entrySet()) {
                jdbc.update("insert into build_feature_effects(feature_id,effect_key,effect_value) values(:id,:key,:value)",
                        Map.of("id",id,"key",effect.getKey(),"value",((Number)effect.getValue()).doubleValue()));
            }
        }
        jdbc.update("delete from ship_rate_weapon_class_rules", Map.of());
        for (Map<String,Object> item : SeedCatalog.listOfMaps(rules.get("ship_rate_weapon_classes"))) {
            Long weaponClass = optionalId("weapon_classes", "code", text(item,"weapon_class"));
            jdbc.update("insert into ship_rate_weapon_class_rules(rate,weapon_class_id) values(:rate,:class)",
                    Map.of("rate",integer(item,"rate",7),"class",weaponClass));
        }
    }

    private void seedBuildRoles() {
        List<Map<String,Object>> roles = List.of(
                Map.of("slug","balanced","label","Balanced","description","General-purpose build","sort",10),
                Map.of("slug","boarding","label","Boarding","description","Boarding and crew pressure","sort",20),
                Map.of("slug","gunnery","label","Gunnery","description","Weapon damage and reload","sort",30),
                Map.of("slug","defensive","label","Defensive","description","Durability and survivability","sort",40));
        for (Map<String,Object> role : roles) jdbc.update("""
                insert into build_roles(slug,label,description,sort_order,created_at,updated_at)
                values(:slug,:label,:description,:sort,:now,:now)
                on conflict(slug) do nothing
                """, Map.of("slug",role.get("slug"),"label",role.get("label"),"description",role.get("description"),
                        "sort",role.get("sort"),"now",now()));
    }

    private boolean overridden(String table, long id) {
        if (!List.of("build_item_options","ships").contains(table)) throw new IllegalArgumentException("Unsupported table");
        return jdbc.count("select count(*) from " + table + " where id=:id and is_seed_overridden=true", Map.of("id",id)) > 0;
    }

    private long requiredId(String table, String column, String value) {
        if (!List.of("build_item_categories","ships","build_features").contains(table)
                || !List.of("key","name","code").contains(column)) throw new IllegalArgumentException("Unsupported lookup");
        return jdbc.optional("select id from " + table + " where " + column + "=:value", Map.of("value",value))
                .map(row -> longValue(row,"id")).orElseThrow(() -> new IllegalStateException("Required seed dependency is missing."));
    }

    private Long optionalId(String table, String column, String value) {
        if (value == null || value.isBlank()) return null;
        if (!List.of("weapon_classes","weapon_slot_types").contains(table) || !List.of("code").contains(column)) {
            throw new IllegalArgumentException("Unsupported lookup");
        }
        return jdbc.optional("select id from " + table + " where " + column + "=:value", Map.of("value",value))
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

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
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
