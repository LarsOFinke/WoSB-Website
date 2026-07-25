"""Declarative Build Designer stat catalog.

Keeping stat metadata separate from arithmetic makes catalog changes reviewable
without coupling them to calculation code.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatDefinition:
    key: str
    label: str
    category: str
    base_field: str | None = None
    unit: str | None = None
    pct_effect: str | None = None
    flat_effect: str | None = None
    calculation_flat_effect: str | None = None
    precision: int = 0
    positive_is_good: bool = True
    source: str = "ship_catalog"
    pct_base_field: str | None = None


STAT_DEFINITIONS: tuple[StatDefinition, ...] = (
    StatDefinition("durability", "Durability", "survivability", "durability", pct_effect="hull_hp_pct", calculation_flat_effect="durability", precision=0),
    StatDefinition("durability_bonus", "Durability bonus", "survivability", flat_effect="durability", precision=0, source="upgrade_modifiers"),
    StatDefinition("speed_min_knots", "Base speed", "mobility", "speed_min_knots", unit="kn", pct_effect="speed_pct", precision=1),
    StatDefinition("speed_knots", "Cruise max. speed", "mobility", "speed_knots", unit="kn", pct_effect="speed_pct", calculation_flat_effect="speed_knots", precision=1, pct_base_field="speed_min_knots"),
    StatDefinition("speed_bonus_knots", "Speed bonus", "mobility", unit="kn", flat_effect="speed_knots", precision=1, source="equipment_modifiers"),
    StatDefinition("cruising_speed_gain_pct", "Cruising speed gain", "mobility", unit="%", flat_effect="cruising_speed_gain_pct", precision=0, source="equipment_modifiers"),
    StatDefinition("cruising_maneuverability_pct", "Cruising maneuverability", "mobility", unit="%", flat_effect="cruising_maneuverability_pct", precision=0, source="equipment_modifiers"),
    StatDefinition("cruising_turn_speed_penalty_pct", "Cruising turn speed", "mobility", unit="%", flat_effect="cruising_turn_speed_penalty_pct", precision=0, source="equipment_modifiers"),
    StatDefinition("strong_wind_cruising_speed_bonus_knots", "Strong-wind cruising speed", "mobility", unit="kn", flat_effect="strong_wind_cruising_speed_bonus_knots", precision=1, source="equipment_modifiers"),
    StatDefinition("turning_cruising_speed_bonus_knots", "Turning cruising-speed bonus", "mobility", unit="kn", flat_effect="turning_cruising_speed_bonus_knots", precision=1, source="equipment_modifiers"),
    StatDefinition("running_before_wind_speed_penalty_pct", "Running-before-wind speed", "mobility", unit="%", flat_effect="running_before_wind_speed_penalty_pct", precision=0, source="equipment_modifiers"),
    StatDefinition("broad_reach_cruising_speed_bonus_pct", "Broad-reach cruising bonus", "mobility", unit="%", flat_effect="broad_reach_cruising_speed_bonus_pct", precision=0, source="equipment_modifiers"),
    StatDefinition("maneuverability", "Maneuverability", "mobility", "maneuverability", pct_effect="turn_rate_pct", calculation_flat_effect="maneuverability", precision=0),
    StatDefinition("maneuverability_bonus", "Maneuverability bonus", "mobility", flat_effect="maneuverability", precision=0, source="equipment_modifiers"),
    StatDefinition("armor", "Broadside armor", "survivability", "armor", pct_effect="armor_pct", calculation_flat_effect="armor", precision=1),
    StatDefinition("armor_bonus", "Armor bonus", "survivability", flat_effect="armor", precision=0, source="upgrade_modifiers"),
    StatDefinition("hold_capacity", "Cargo hold", "logistics", "hold_capacity", unit="t", pct_effect="hold_capacity_pct", calculation_flat_effect="hold_capacity", precision=0),
    StatDefinition("hold_capacity_bonus", "Cargo hold bonus", "logistics", unit="t", flat_effect="hold_capacity", precision=0, source="upgrade_modifiers"),
    StatDefinition("crew_capacity", "Crew capacity", "crew", "crew_capacity", pct_effect="crew_capacity_pct", calculation_flat_effect="crew_capacity", precision=0),
    StatDefinition("crew_capacity_bonus", "Crew capacity bonus", "crew", flat_effect="crew_capacity", precision=0, source="upgrade_modifiers"),
    StatDefinition("sailor_minimum", "Sailing crew target", "crew", "sailor_minimum", flat_effect="sailor_minimum", precision=0, positive_is_good=False),
    StatDefinition("displacement_tons", "Displacement", "ship", "displacement_tons", unit="t", precision=0),
    StatDefinition("reload_pct", "Reload speed", "combat", unit="%", flat_effect="reload_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("weapon_range_pct", "Cannon range", "combat", unit="%", flat_effect="weapon_range_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("damage_pct", "Damage", "combat", unit="%", flat_effect="damage_pct", precision=0, source="equipment_modifiers"),
    StatDefinition("cannon_damage_pct", "Cannon damage", "combat", unit="%", flat_effect="cannon_damage_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("low_hp_damage_pct", "Damage below 50% HP", "combat", unit="%", flat_effect="low_hp_damage_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("fire_damage_pct", "Fire damage", "combat", unit="%", flat_effect="fire_damage_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("mortar_range_pct", "Mortar range", "siege", unit="%", flat_effect="mortar_range_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("siege_damage_pct", "Siege damage", "siege", unit="%", flat_effect="siege_damage_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("ram_damage_pct", "Ram damage", "combat", unit="%", flat_effect="ram_damage_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("boarding_power_pct", "Boarding power", "boarding", unit="%", flat_effect="boarding_power_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("repair_efficiency_pct", "Repair efficiency", "survivability", unit="%", flat_effect="repair_efficiency_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("sail_hp_pct", "Sail durability", "survivability", unit="%", flat_effect="sail_hp_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("fire_resistance_pct", "Fire resistance", "survivability", unit="%", flat_effect="fire_resistance_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("cargo_loss_reduction_pct", "Cargo loss reduction", "logistics", unit="%", flat_effect="cargo_loss_reduction_pct", precision=0, source="upgrade_modifiers"),
    StatDefinition("exp_loot_pct", "Experience and loot", "rewards", unit="%", flat_effect="exp_loot_pct", precision=0, source="equipment_modifiers"),
    StatDefinition("hold_slots", "Hold slots", "logistics", flat_effect="hold_slots", precision=0, source="upgrade_modifiers"),
    StatDefinition("extra_upgrade_slots", "Extra upgrade slots", "equipment", flat_effect="extra_upgrade_slots", precision=0, source="upgrade_modifiers"),
    StatDefinition("fire_risk_pct", "Fire risk", "risk", unit="%", flat_effect="fire_risk_pct", precision=0, positive_is_good=False, source="upgrade_modifiers"),
    StatDefinition("sail_efficiency", "Additional sail efficiency", "mobility", flat_effect="sail_efficiency", source="upgrade_modifiers"),
    StatDefinition("reeling_speed_pct", "Reeling speed", "expeditionary", unit="%", flat_effect="reeling_speed_pct", source="upgrade_modifiers"),
    StatDefinition("boarding_range_pct", "Boarding range", "boarding", unit="%", flat_effect="boarding_range_pct", source="upgrade_modifiers"),
    StatDefinition("item_loss_pct", "Item loss", "logistics", unit="%", flat_effect="item_loss_pct", positive_is_good=False, source="upgrade_modifiers"),
    StatDefinition("ship_roll_reduction_pct", "Ship roll reduction", "combat", unit="%", flat_effect="ship_roll_reduction_pct", source="upgrade_modifiers"),
    StatDefinition("weapon_spread_pct", "Weapon spread", "combat", unit="%", flat_effect="weapon_spread_pct", positive_is_good=False, source="upgrade_modifiers"),
    StatDefinition("perishable_goods_preserved_enabled", "Perishable goods do not spoil", "logistics", flat_effect="perishable_goods_preserved_enabled", source="upgrade_modifiers"),
    StatDefinition("crew_count_hidden_enabled", "Crew count hidden", "crew", flat_effect="crew_count_hidden_enabled", source="upgrade_modifiers"),
    StatDefinition("repair_item_efficiency_pct", "Repair item efficiency", "survivability", unit="%", flat_effect="repair_item_efficiency_pct", source="upgrade_modifiers"),
    StatDefinition("water_fire_protection_pct", "Water-fire protection", "survivability", unit="%", flat_effect="water_fire_protection_pct", source="upgrade_modifiers"),
    StatDefinition("explosive_fire_ship_protection_pct", "Gunpowder barrel and fire-ship protection", "survivability", unit="%", flat_effect="explosive_fire_ship_protection_pct", source="upgrade_modifiers"),
    StatDefinition("bow_damage_absorption_pct", "Bow damage absorption", "survivability", unit="%", flat_effect="bow_damage_absorption_pct", source="upgrade_modifiers"),
    StatDefinition("quick_sinking_by_ramming_enabled", "Quick sinking by ramming", "combat", flat_effect="quick_sinking_by_ramming_enabled", source="upgrade_modifiers"),
    StatDefinition("sail_protection_pct", "Sail protection", "survivability", unit="%", flat_effect="sail_protection_pct", source="upgrade_modifiers"),
    StatDefinition("sail_fire_protection_pct", "Sail fire protection", "survivability", unit="%", flat_effect="sail_fire_protection_pct", source="upgrade_modifiers"),
    StatDefinition("barrel_reload_pct", "Barrel reload speed", "combat", unit="%", flat_effect="barrel_reload_pct", source="upgrade_modifiers"),
    StatDefinition("swivel_gun_reload_pct", "Swivel-gun reload speed", "combat", unit="%", flat_effect="swivel_gun_reload_pct", source="upgrade_modifiers"),
    StatDefinition("weapon_angle", "Weapon angle", "combat", flat_effect="weapon_angle", source="upgrade_modifiers"),
    StatDefinition("bow_stern_weapon_damage_pct", "Bow and stern weapon damage", "combat", unit="%", flat_effect="bow_stern_weapon_damage_pct", source="upgrade_modifiers"),
    StatDefinition("all_ammo_ignition_enabled", "Fire effects with every ammunition type", "combat", flat_effect="all_ammo_ignition_enabled", source="upgrade_modifiers"),
    StatDefinition("projectile_speed_pct", "Projectile speed", "combat", unit="%", flat_effect="projectile_speed_pct", source="upgrade_modifiers"),
    StatDefinition("weapon_range", "Cannon range", "combat", flat_effect="weapon_range", source="upgrade_modifiers"),
    StatDefinition("mortar_protection_pct", "Mortar protection", "survivability", unit="%", flat_effect="mortar_protection_pct", source="upgrade_modifiers"),
    StatDefinition("boarding_gold_pct", "Gold from successful boarding", "rewards", unit="%", flat_effect="boarding_gold_pct", source="upgrade_modifiers"),
    StatDefinition("barrels_mines_third_speed_enabled", "Barrels and mines at third speed", "combat", flat_effect="barrels_mines_third_speed_enabled", source="upgrade_modifiers"),
    StatDefinition("barrel_mine_radius_pct", "Barrel and mine damage radius", "combat", unit="%", flat_effect="barrel_mine_radius_pct", source="upgrade_modifiers"),
    StatDefinition("mortar_range", "Mortar range", "siege", flat_effect="mortar_range", source="upgrade_modifiers"),
    StatDefinition("mortar_dead_zone_reduction_pct", "Mortar dead-zone reduction", "siege", unit="%", flat_effect="mortar_dead_zone_reduction_pct", source="upgrade_modifiers"),
    StatDefinition("mortar_reload_pct", "Mortar reload speed", "siege", unit="%", flat_effect="mortar_reload_pct", source="upgrade_modifiers"),
    StatDefinition("mortar_damage_pct", "Mortar damage", "siege", unit="%", flat_effect="mortar_damage_pct", source="upgrade_modifiers"),
    StatDefinition("mortar_angle_degrees", "Mortar angle", "siege", unit="°", flat_effect="mortar_angle_degrees", source="upgrade_modifiers"),
    # Specialist effects transcribed from the in-game tooltip catalog. Raw
    # per-crew keys are exposed for option summaries; effective derived keys are
    # produced by specialist_effect_service for the live calculator.
    StatDefinition("all_experience_pct", "All experience", "rewards", unit="%", flat_effect="all_experience_pct", source="specialist_modifiers"),
    StatDefinition("branch_upgrade_experience_pct", "Ship branch and upgrade experience", "rewards", unit="%", flat_effect="branch_upgrade_experience_pct", source="specialist_modifiers"),
    StatDefinition("visibility_range_pct", "Visibility range", "utility", unit="%", flat_effect="visibility_range_pct", source="specialist_modifiers"),
    StatDefinition("minimap_item_visibility_pct", "Minimap item visibility", "utility", unit="%", flat_effect="minimap_item_visibility_pct", source="specialist_modifiers"),
    StatDefinition("boarding_hook_reload_pct", "Boarding hook reload speed", "boarding", unit="%", flat_effect="boarding_hook_reload_pct", source="specialist_modifiers"),
    StatDefinition("boarding_cargo_weight_per_boarder_pct", "Boarding cargo weight per boarder", "boarding", unit="%", flat_effect="boarding_cargo_weight_per_boarder_pct", precision=1, source="specialist_catalog"),
    StatDefinition("boarding_cargo_weight_pct", "Boarding cargo weight", "boarding", unit="%", flat_effect="boarding_cargo_weight_pct", precision=1, source="specialist_modifiers"),
    StatDefinition("crew_pickup_limit", "Crew pickup limit", "crew", flat_effect="crew_pickup_limit", source="specialist_modifiers"),
    StatDefinition("swivel_reload_pct", "Swivel gun reload speed", "combat", unit="%", flat_effect="swivel_reload_pct", source="specialist_modifiers"),
    StatDefinition("sortie_death_prevention_enabled", "No crew deaths in sorties", "boarding", flat_effect="sortie_death_prevention_enabled", source="specialist_modifiers"),
    StatDefinition("boarding_company_shelling_survivability_pct", "Boarding-company survivability during shelling", "boarding", unit="%", flat_effect="boarding_company_shelling_survivability_pct", source="specialist_modifiers"),
    StatDefinition("single_random_boarding_target_enabled", "Single random target at boarding start", "boarding", flat_effect="single_random_boarding_target_enabled", source="specialist_modifiers"),
    StatDefinition("item_pickup_range_pct", "Item pick-up range", "utility", unit="%", flat_effect="item_pickup_range_pct", source="specialist_modifiers"),
    StatDefinition("post_boarding_crew_healing_pct", "Crew healing after boarding", "crew", unit="%", flat_effect="post_boarding_crew_healing_pct", source="specialist_modifiers"),
    StatDefinition("speed_per_sailor_pct", "Speed per Sailor", "mobility", unit="%", flat_effect="speed_per_sailor_pct", precision=1, source="specialist_catalog"),
    StatDefinition("stationary_first_speed_maneuverability", "Maneuverability while stationary and at first speed", "mobility", flat_effect="stationary_first_speed_maneuverability", source="specialist_modifiers"),
    StatDefinition("low_durability_maneuverability", "Maneuverability at 50% durability or lower", "mobility", flat_effect="low_durability_maneuverability", source="specialist_modifiers"),
    StatDefinition("sail_autorepair_pct", "Sail auto-repair speed", "survivability", unit="%", flat_effect="sail_autorepair_pct", source="specialist_modifiers"),
    StatDefinition("second_speed_repair_enabled", "Repairs available at second speed", "survivability", flat_effect="second_speed_repair_enabled", source="specialist_modifiers"),
    StatDefinition("animal_slaughter_for_food_enabled", "Animal slaughter for food", "crew", flat_effect="animal_slaughter_for_food_enabled", source="specialist_modifiers"),
    StatDefinition("overload_speed_penalty_reduction_pct", "Overload speed-penalty reduction", "logistics", unit="%", flat_effect="overload_speed_penalty_reduction_pct", source="specialist_modifiers"),
    StatDefinition("food_nutrition_pct", "Food nutrition", "crew", unit="%", flat_effect="food_nutrition_pct", source="specialist_modifiers"),
    StatDefinition("weapon_explosion_risk_reduction_pct", "Weapon explosion-risk reduction", "combat", unit="%", flat_effect="weapon_explosion_risk_reduction_pct", source="specialist_modifiers"),
    StatDefinition("fishing_catch_per_boarder_pct", "Fishing catch per boarder", "rewards", unit="%", flat_effect="fishing_catch_per_boarder_pct", precision=1, source="specialist_catalog"),
    StatDefinition("fishing_catch_pct", "Whale-hunting and fishing catch", "rewards", unit="%", flat_effect="fishing_catch_pct", precision=1, source="specialist_modifiers"),
    StatDefinition("fishing_speed_per_sailor_pct", "Fishing speed per Sailor", "rewards", unit="%", flat_effect="fishing_speed_per_sailor_pct", source="specialist_catalog"),
    StatDefinition("fishing_speed_pct", "Fishing speed", "rewards", unit="%", flat_effect="fishing_speed_pct", source="specialist_modifiers"),
    StatDefinition("repair_speed_per_sailor_pct", "Repair speed per Sailor", "survivability", unit="%", flat_effect="repair_speed_per_sailor_pct", precision=1, source="specialist_catalog"),
    StatDefinition("repair_speed_pct", "Repair speed", "survivability", unit="%", flat_effect="repair_speed_pct", precision=1, source="specialist_modifiers"),
    StatDefinition("steady_course_enabled", "Steady-course assistance", "mobility", flat_effect="steady_course_enabled", source="specialist_modifiers"),
    StatDefinition("boarding_musketeer_defense_enabled", "Musketeers start defending during boarding", "boarding", flat_effect="boarding_musketeer_defense_enabled", source="specialist_modifiers"),
    StatDefinition("fire_extinguishing_pct", "Fire-extinguishing speed", "survivability", unit="%", flat_effect="fire_extinguishing_pct", source="specialist_modifiers"),
    StatDefinition("large_fire_damage_pct", "Large-fire damage", "survivability", unit="%", flat_effect="large_fire_damage_pct", source="specialist_modifiers"),
    StatDefinition("microfire_extinguishing_pct", "Microfire extinguishing speed", "survivability", unit="%", flat_effect="microfire_extinguishing_pct", source="specialist_modifiers"),
    StatDefinition("repair_wounded_crew_pct", "Wounded crew healed during repairs", "crew", unit="%", flat_effect="repair_wounded_crew_pct", source="specialist_modifiers"),
    StatDefinition("item_reload_per_sailor_pct", "Item reload per Sailor", "combat", unit="%", flat_effect="item_reload_per_sailor_pct", precision=1, source="specialist_catalog"),
    StatDefinition("item_reload_pct", "Item reload speed", "combat", unit="%", flat_effect="item_reload_pct", precision=1, source="specialist_modifiers"),
    StatDefinition("npc_grapeshot_damage_pct", "Grapeshot damage against NPCs", "combat", unit="%", flat_effect="npc_grapeshot_damage_pct", source="specialist_modifiers"),
    StatDefinition("weapon_aiming_pct", "Weapon aiming speed", "combat", unit="%", flat_effect="weapon_aiming_pct", source="specialist_modifiers"),
    StatDefinition("ammo_switch_per_sailor_pct", "Ammunition switch speed per Sailor", "combat", unit="%", flat_effect="ammo_switch_per_sailor_pct", precision=1, source="specialist_catalog"),
    StatDefinition("ammo_switch_speed_pct", "Ammunition switch speed", "combat", unit="%", flat_effect="ammo_switch_speed_pct", precision=1, source="specialist_modifiers"),
    StatDefinition("next_single_shot_reload_pct", "Next reload after a single cannon shot", "combat", unit="%", flat_effect="next_single_shot_reload_pct", source="specialist_modifiers"),
    StatDefinition("low_durability_reload_per_sailor_pct", "Low-durability reload speed per Sailor", "combat", unit="%", flat_effect="low_durability_reload_per_sailor_pct", precision=1, source="specialist_catalog"),
    StatDefinition("low_durability_reload_pct", "Reload speed at 50% durability or lower", "combat", unit="%", flat_effect="low_durability_reload_pct", precision=1, source="specialist_modifiers"),
    StatDefinition("mortar_aiming_pct", "Mortar aiming speed", "siege", unit="%", flat_effect="mortar_aiming_pct", source="specialist_modifiers"),
    StatDefinition("loaded_weapons_mortar_reload_pct", "Mortar reload speed while weapons are loaded", "siege", unit="%", flat_effect="loaded_weapons_mortar_reload_pct", source="specialist_modifiers"),
    StatDefinition("unique_crew_empire_boarding_chance_pct", "Unique crew chance when boarding Empire ships", "rewards", unit="%", flat_effect="unique_crew_empire_boarding_chance_pct", source="specialist_modifiers"),
    StatDefinition("unique_crew_at_sea_chance_pct", "Unique crew chance at sea", "rewards", unit="%", flat_effect="unique_crew_at_sea_chance_pct", source="specialist_modifiers"),
    StatDefinition("unique_crew_save_after_mode_pct", "Unique crew recovery after mode completion", "rewards", unit="%", flat_effect="unique_crew_save_after_mode_pct", source="specialist_modifiers"),
    StatDefinition("boarding_captives_pct", "Boarding captives", "boarding", unit="%", flat_effect="boarding_captives_pct", source="specialist_modifiers"),
    StatDefinition("double_items_at_sea_chance_pct", "Double items at sea chance", "rewards", unit="%", flat_effect="double_items_at_sea_chance_pct", source="specialist_modifiers"),
    StatDefinition("rare_items_chance_pct", "Rare items chance", "rewards", unit="%", flat_effect="rare_items_chance_pct", source="specialist_modifiers"),
    StatDefinition("consumables_no_port_timer_enabled", "No consumable timer before entering port", "utility", flat_effect="consumables_no_port_timer_enabled", source="specialist_modifiers"),
    StatDefinition("shipwreck_durability_restore_pct", "Durability restored at shipwrecks", "survivability", unit="%", flat_effect="shipwreck_durability_restore_pct", source="specialist_modifiers"),
    StatDefinition("conflict_resolution_enabled", "Specialist conflict resolution", "crew", flat_effect="conflict_resolution_enabled", source="specialist_modifiers"),
)

DEFINITION_BY_EFFECT_KEY: dict[str, StatDefinition] = {
    effect_key: definition
    for definition in STAT_DEFINITIONS
    for effect_key in (definition.pct_effect, definition.flat_effect)
    if effect_key
}


