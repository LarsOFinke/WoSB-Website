package eu.royalblackwater.api.masterdata.repository.queries;

/** SQL statements owned by the MasterDataMutationService persistence boundary. */
public final class MasterDataMutationQueries {
    private MasterDataMutationQueries() { }

    public static final String CREATE_CATEGORY_INSERT_01 = """
                insert into build_item_categories(key,label,sort_order,is_active,is_seed_overridden,created_at,updated_at)
                values(:key,:label,:sort,:active,false,:now,:now) returning id
                """;

    public static final String UPDATE_CATEGORY_UPDATE_01 = """
                update build_item_categories set label=:label,sort_order=:sort,is_active=:active,
                    is_seed_overridden=case when seed_key is null then false else true end,updated_at=:now where id=:id
                """;

    public static final String DELETE_CATEGORY_SELECT_01 = "select count(*) from build_item_options where category_id=:id";

    public static final String DELETE_CATEGORY_DELETE_01 = "delete from build_item_categories where id=:id";

    public static final String RESTORE_CATEGORY_UPDATE_01 = "update build_item_categories set is_seed_overridden=false where id=:id";

    public static final String UPDATE_OPTION_UPDATE_01 = "update build_item_options set is_seed_overridden=seed_key is not null where id=:id";

    public static final String DELETE_OPTION_SELECT_01 = """
                select (select count(*) from build_slots where option_id=:id)
                     +(select count(*) from ship_upgrade_effect_overrides where option_id=:id)
                """;

    public static final String DELETE_OPTION_DELETE_01 = "delete from build_item_options where id=:id";

    public static final String RESTORE_OPTION_UPDATE_01 = "update build_item_options set is_seed_overridden=false where id=:id";

    public static final String UPDATE_SHIP_UPDATE_01 = """
                update ships set name=:name,rate=:rate,ship_type=:type,durability=:durability,
                    speed_min_knots=:speedMin,speed_knots=:speed,maneuverability=:maneuver,armor=:armor,
                    hold_capacity=:hold,crew_capacity=:crew,sailor_minimum=:sailors,displacement_tons=:displacement,
                    source=:source,image_url=:image,sail_slots=:sails,upgrade_slots=:upgrades,has_lantern=:lantern,
                    is_active=:active,is_seed_overridden=seed_key is not null,updated_at=:now where id=:id
                """;

    public static final String DELETE_SHIP_SELECT_01 = "select count(*) from builds where ship_id=:id";

    public static final String DELETE_SHIP_DELETE_01 = "delete from ships where id=:id";

    public static final String RESTORE_SHIP_UPDATE_01 = "update ships set is_seed_overridden=false where id=:id";

    public static final String WRITE_OPTION_INSERT_01 = """
                insert into build_item_options(category_id,name,source,notes,image_url,option_kind,weapon_class_id,
                    weapon_caliber_inches,sort_order,is_active,is_seed_overridden,created_at,updated_at)
                values(:category,:name,:source,:notes,:image,:kind,:class,:caliber,:sort,:active,false,:now,:now) returning id
                """;

    public static final String WRITE_OPTION_UPDATE_01 = """
                update build_item_options set category_id=:category,name=:name,source=:source,notes=:notes,
                    image_url=:image,option_kind=:kind,weapon_class_id=:class,weapon_caliber_inches=:caliber,
                    sort_order=:sort,is_active=:active,updated_at=:now where id=:id
                """;

    public static final String REPLACE_OPTION_CHILDREN_DELETE_01 = "delete from build_item_effects where option_id=:id";

    public static final String REPLACE_OPTION_CHILDREN_INSERT_01 = "insert into build_item_effects(option_id,effect_key,effect_value) values(:id,:key,:value)";

    public static final String REPLACE_OPTION_CHILDREN_DELETE_02 = "delete from build_item_option_slot_types where option_id=:id";

    public static final String REPLACE_OPTION_CHILDREN_INSERT_02 = """
                insert into build_item_option_slot_types(option_id,slot_type_id)
                select :id,id from weapon_slot_types where code=:code
                """;

    public static final String REPLACE_OPTION_CHILDREN_DELETE_03 = "delete from weapon_performance_profiles where option_id=:id";

    public static final String REPLACE_OPTION_CHILDREN_INSERT_03 = "insert into weapon_performance_profiles(option_id,base_damage,reload_seconds) values(:id,:damage,:reload)";

    public static final String WRITE_SHIP_INSERT_01 = """
                insert into ships(name,rate,ship_type,durability,speed_min_knots,speed_knots,maneuverability,armor,
                    hold_capacity,crew_capacity,sailor_minimum,displacement_tons,source,image_url,sail_slots,upgrade_slots,
                    has_lantern,is_active,is_seed_overridden,created_at,updated_at)
                values(:name,:rate,:type,:durability,:speedMin,:speed,:maneuver,:armor,:hold,:crew,:sailors,:displacement,
                    :source,:image,:sails,:upgrades,:lantern,:active,false,:now,:now) returning id
                """;

    public static final String REPLACE_SHIP_CHILDREN_DELETE_01 = "delete from ship_weapon_mounts where ship_id=:id";

    public static final String REPLACE_SHIP_CHILDREN_INSERT_01 = """
                insert into ship_weapon_mounts(ship_id,slot_type_id,capacity,special_weapon_capacity,max_weapon_class_id,max_caliber_inches)
                select :ship,slot.id,:capacity,:special,wc.id,:caliber from weapon_slot_types slot
                left join weapon_classes wc on wc.code=:class where slot.code=:slot
                """;

    public static final String REPLACE_SHIP_CHILDREN_DELETE_02 = "delete from ship_mortar_modifications where ship_id=:id";

    public static final String REPLACE_SHIP_CHILDREN_INSERT_02 = """
                insert into ship_mortar_modifications(ship_id,mortar_capacity,max_caliber_inches,broadside_capacity_delta,
                    durability_delta,speed_pct,maneuverability_delta,hold_capacity_pct,crew_capacity_delta,source)
                values(:id,:capacity,:caliber,:broadside,:durability,:speed,:maneuver,:hold,:crew,:source)
                """;

    public static final String REPLACE_SHIP_CHILDREN_DELETE_03 = "delete from ship_upgrade_effect_overrides where ship_id=:id";

    public static final String REPLACE_SHIP_CHILDREN_INSERT_03 = """
                        insert into ship_upgrade_effect_overrides(ship_id,option_id,effect_key,effect_value,created_at,updated_at)
                        values(:ship,:option,:key,:value,:now,:now)
                        """;

    public static final String REQUIRE_SELECT_01 = "select count(*) from ";

    public static final String REQUIRE_WHERE_01 = " where id=:id";

    public static final String REQUIRE_SEEDED_WHERE_01 = " where id=:id and seed_key is not null";

    public static final String LOOKUP_SELECT_01 = "select id from weapon_classes where code=:code";

}
