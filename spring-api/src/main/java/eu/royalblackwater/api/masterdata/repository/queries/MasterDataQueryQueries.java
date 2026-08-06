package eu.royalblackwater.api.masterdata.repository.queries;

/** SQL statements owned by the MasterDataQueryService persistence boundary. */
public final class MasterDataQueryQueries {
    private MasterDataQueryQueries() { }

    public static final String OVERVIEW_SELECT_01 = "select count(*) from build_item_categories";

    public static final String OVERVIEW_SELECT_02 = """
                        select (select count(*) from build_item_categories where not is_active)
                             + (select count(*) from build_item_options where not is_active)
                             + (select count(*) from ships where not is_active)
                        """;

    public static final String OVERVIEW_SELECT_03 = "select count(*) from build_item_options";

    public static final String OVERVIEW_SELECT_04 = """
                        select (select count(*) from build_item_categories where is_seed_overridden)
                             + (select count(*) from build_item_options where is_seed_overridden)
                             + (select count(*) from ships where is_seed_overridden)
                        """;

    public static final String OVERVIEW_SELECT_05 = "select count(*) from ships";

    public static final String CATEGORIES_SELECT_01 = "select * from build_item_categories order by sort_order,key,id";

    public static final String OPTIONS_SELECT_01 = """
                select link.option_id, type.code
                  from build_item_option_slot_types link
                  join weapon_slot_types type on type.id=link.slot_type_id
                 order by link.option_id,type.sort_order,type.code
                """;

    public static final String OPTIONS_SELECT_02 = "select option_id,effect_key,effect_value from build_item_effects order by option_id,effect_key";

    public static final String SHIPS_SELECT_01 = "select * from ships order by rate,name,id";

    public static final String CATEGORY_SELECT_01 = "select * from build_item_categories where id=:id";

    public static final String OPTION_SELECT_01 = """
                select link.option_id, type.code
                  from build_item_option_slot_types link
                  join weapon_slot_types type on type.id=link.slot_type_id
                 where link.option_id in (:ids)
                 order by link.option_id,type.sort_order,type.code
                """;

    public static final String OPTION_SELECT_02 = """
                select option_id,effect_key,effect_value
                  from build_item_effects
                 where option_id in (:ids)
                 order by option_id,effect_key
                """;

    public static final String SHIP_SELECT_01 = "select * from ships where id=:id";

    public static final String TAXONOMY_SELECT_01 = "select code,label,rank from weapon_classes order by rank,code";

    public static final String TAXONOMY_SELECT_02 = "select code,label,sort_order from weapon_slot_types order by sort_order,code";

    public static final String TAXONOMY_SELECT_03 = """
                select rule.rate,wc.code weapon_class
                  from ship_rate_weapon_class_rules rule
                  join weapon_classes wc on wc.id=rule.weapon_class_id
                 order by rule.rate
                """;

    public static final String OPTION_ROWS_WHERE_01 = " where o.id=:id";

    public static final String OPTION_ROWS_SELECT_01 = """
                select o.*, c.key category_key, c.label category_label, wc.code weapon_class,
                       wp.base_damage, wp.reload_seconds
                  from build_item_options o
                  join build_item_categories c on c.id=o.category_id
                  left join weapon_classes wc on wc.id=o.weapon_class_id
                  left join weapon_performance_profiles wp on wp.option_id=o.id
                """;

    public static final String OPTION_ROWS_ORDER_BY_01 = " order by c.sort_order,o.sort_order,o.name,o.id";

    public static final String ASSEMBLE_SHIPS_SELECT_01 = """
                select m.ship_id,type.code slot_type,m.capacity,m.special_weapon_capacity,
                       wc.code max_weapon_class,m.max_caliber_inches
                  from ship_weapon_mounts m
                  join weapon_slot_types type on type.id=m.slot_type_id
                  left join weapon_classes wc on wc.id=m.max_weapon_class_id
                 where m.ship_id in (:ids)
                 order by m.ship_id,type.sort_order,type.code
                """;

    public static final String ASSEMBLE_SHIPS_SELECT_02 = "select * from ship_mortar_modifications where ship_id in (:ids)";

    public static final String ASSEMBLE_SHIPS_SELECT_03 = """
                select value.ship_id,value.option_id,option.name option_name,value.effect_key,value.effect_value
                  from ship_upgrade_effect_overrides value
                  join build_item_options option on option.id=value.option_id
                 where value.ship_id in (:ids)
                 order by value.ship_id,value.option_id,value.effect_key
                """;

}
