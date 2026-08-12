package eu.royalblackwater.api.masterdata.repository.queries;

/** SQL statements owned by the ReferenceDataSeeder persistence boundary. */
public final class ReferenceDataQueries {
    private ReferenceDataQueries() { }

    public static final String SEED_SYSTEM_DATA_INSERT_01 = """
                    insert into site_roles(code,label,rank,is_staff,can_manage_system,created_at)
                    values(:code,:label,:rank,:staff,:system,:now)
                    on conflict(code) do update set label=excluded.label,rank=excluded.rank,
                        is_staff=excluded.is_staff,can_manage_system=excluded.can_manage_system
                    """;

    public static final String SEED_SYSTEM_DATA_INSERT_02 = """
                    insert into fleet_roles(code,label,rank,is_leadership,can_manage_fleet,can_manage_members,
                        is_system,is_active,created_at,updated_at)
                    values(:code,:label,:rank,:leadership,:manageFleet,:manageMembers,:system,:active,:now,:now)
                    on conflict(code) do update set label=excluded.label,rank=excluded.rank,
                        is_leadership=excluded.is_leadership,can_manage_fleet=excluded.can_manage_fleet,
                        can_manage_members=excluded.can_manage_members,is_system=excluded.is_system,
                        is_active=excluded.is_active,updated_at=excluded.updated_at
                    """;

    public static final String SEED_SYSTEM_DATA_INSERT_03 = """
                    insert into squad_roles(code,label,rank,can_manage_roster,can_manage_events,created_at)
                    values(:code,:label,:rank,:roster,:events,:now)
                    on conflict(code) do update set label=excluded.label,rank=excluded.rank,
                        can_manage_roster=excluded.can_manage_roster,can_manage_events=excluded.can_manage_events
                    """;

    public static final String SEED_SYSTEM_DATA_INSERT_04 = """
                    insert into fleets(name,slug,focus,description,standing_orders,sort_order,is_active,created_at,updated_at)
                    values(:name,:slug,:focus,:description,:orders,:sort,true,:now,:now)
                    on conflict(slug) do update set name=excluded.name,focus=excluded.focus,
                        description=excluded.description,standing_orders=excluded.standing_orders,
                        sort_order=excluded.sort_order,is_active=true,updated_at=excluded.updated_at
                    """;

    public static final String SEED_TAXONOMY_INSERT_01 = """
                    insert into weapon_classes(code,label,rank) values(:code,:label,:rank)
                    on conflict(code) do update set label=excluded.label, rank=excluded.rank
                    """;

    public static final String SEED_TAXONOMY_INSERT_02 = """
                    insert into weapon_slot_types(code,label,sort_order) values(:code,:label,:sort)
                    on conflict(code) do update set label=excluded.label, sort_order=excluded.sort_order
                    """;

    public static final String SEED_CATEGORIES_INSERT_01 = """
                    insert into build_item_categories(key,label,sort_order,is_active,seed_key,seed_revision,
                        seed_checksum,is_seed_overridden,created_at,updated_at)
                    values(:key,:label,:sort,true,:seed,:revision,:checksum,false,:now,:now)
                    on conflict(key) do update set label=excluded.label, sort_order=excluded.sort_order,
                        is_active=true, seed_key=excluded.seed_key, seed_revision=excluded.seed_revision,
                        seed_checksum=excluded.seed_checksum, is_seed_overridden=false, updated_at=excluded.updated_at
                    where :discard or build_item_categories.is_seed_overridden=false
                    """;

    public static final String SEED_OPTIONS_INSERT_01 = """
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
                    """;

    public static final String SEED_OPTIONS_SELECT_01 = "select id from build_item_options where category_id=:category and name=:name";

    public static final String SEED_OPTIONS_SELECT_BY_SEED_KEY_01 =
            "select id from build_item_options where seed_key=:seed";

    public static final String REPLACE_OPTION_CHILDREN_DELETE_01 = "delete from build_item_effects where option_id=:id";

    public static final String REPLACE_OPTION_CHILDREN_INSERT_01 = """
                    insert into build_item_effects(option_id,effect_key,effect_value,created_at,updated_at)
                    values(:id,:key,:value,:now,:now)
                    """;

    public static final String REPLACE_OPTION_CHILDREN_DELETE_02 = "delete from build_item_option_slot_types where option_id=:id";

    public static final String REPLACE_OPTION_CHILDREN_INSERT_02 = "insert into build_item_option_slot_types(option_id,slot_type_id) values(:id,:slot)";

    public static final String REPLACE_OPTION_CHILDREN_DELETE_03 = "delete from weapon_performance_profiles where option_id=:id";

    public static final String REPLACE_OPTION_CHILDREN_INSERT_03 = """
                insert into weapon_performance_profiles(option_id,base_damage,reload_seconds)
                values(:id,:damage,:reload)
                """;

    public static final String SEED_SHIPS_INSERT_01 = """
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
                    """;

    public static final String REPLACE_SHIP_CHILDREN_DELETE_01 = "delete from ship_weapon_mounts where ship_id=:id";

    public static final String REPLACE_SHIP_CHILDREN_INSERT_01 = """
                    insert into ship_weapon_mounts(ship_id,slot_type_id,capacity,special_weapon_capacity,
                        max_weapon_class_id,max_caliber_inches)
                    values(:ship,:slot,:capacity,:special,:class,:caliber)
                    """;

    public static final String REPLACE_SHIP_CHILDREN_DELETE_02 = "delete from ship_mortar_modifications where ship_id=:id";

    public static final String REPLACE_SHIP_CHILDREN_INSERT_02 = """
                insert into ship_mortar_modifications(ship_id,mortar_capacity,max_caliber_inches,
                    broadside_capacity_delta,durability_delta,speed_pct,maneuverability_delta,hold_capacity_pct,
                    crew_capacity_delta,source)
                values(:ship,:capacity,:caliber,:broadside,:durability,:speed,:maneuver,:hold,:crew,:source)
                """;

    public static final String REPLACE_SHIP_CHILDREN_DELETE_03 =
            "delete from ship_upgrade_effect_overrides where ship_id=:id";

    public static final String REPLACE_SHIP_CHILDREN_INSERT_03 = """
            insert into ship_upgrade_effect_overrides(ship_id,option_id,effect_key,effect_value,created_at,updated_at)
            values(:ship,:option,:key,:value,:now,:now)
            """;

    public static final String SEED_BUILD_RULES_INSERT_01 = """
                    insert into build_features(code,label,upgrade_slots_granted,is_active)
                    values(:code,:label,:slots,true) on conflict(code) do update set label=excluded.label,
                    upgrade_slots_granted=excluded.upgrade_slots_granted,is_active=true
                    """;

    public static final String SEED_BUILD_RULES_DELETE_01 = "delete from build_feature_effects where feature_id=:id";

    public static final String SEED_BUILD_RULES_INSERT_02 = "insert into build_feature_effects(feature_id,effect_key,effect_value) values(:id,:key,:value)";

    public static final String SEED_BUILD_RULES_DELETE_02 = "delete from ship_rate_weapon_class_rules";

    public static final String SEED_BUILD_RULES_INSERT_03 = "insert into ship_rate_weapon_class_rules(rate,weapon_class_id) values(:rate,:class)";

    public static final String SEED_BUILD_ROLES_INSERT_01 = """
                insert into build_roles(slug,label,description,sort_order,created_at,updated_at)
                values(:slug,:label,:description,:sort,:now,:now)
                on conflict(slug) do nothing
                """;

    public static final String OVERRIDDEN_SELECT_01 = "select count(*) from ";

    public static final String OVERRIDDEN_WHERE_01 = " where id=:id and is_seed_overridden=true";

    public static final String REQUIRED_ID_SELECT_01 = "select id from ";

    public static final String REQUIRED_ID_WHERE_01 = " where ";

}
