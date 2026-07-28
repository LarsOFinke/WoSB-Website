from app.bootstrap.build_catalog_validation import (
    validate_build_option_catalog,
    validate_lantern_seed_data,
    validate_sail_seed_data,
    validate_special_crew_seed_data,
    validate_upgrade_seed_data,
)
from app.bootstrap.catalog_loader import load_master_data_catalog
from app.modules.builds.services.stat_catalog import STAT_DEFINITIONS


CATALOG = load_master_data_catalog()
BUILD_ITEM_CATEGORIES = [
    row.model_dump(mode="json") for row in CATALOG.build_categories.items
]
OPTIONS_BY_CATEGORY = {
    document.category: [row.model_dump(mode="json") for row in document.items]
    for document in CATALOG.build_options
}
SAIL_OPTIONS = OPTIONS_BY_CATEGORY["sail"]
UPGRADE_OPTIONS = OPTIONS_BY_CATEGORY["upgrade"]
LANTERN_OPTIONS = OPTIONS_BY_CATEGORY["lantern"]
AMMUNITION_OPTIONS = OPTIONS_BY_CATEGORY["ammunition"]
CONSUMABLE_OPTIONS = OPTIONS_BY_CATEGORY["consumable"]
HOLD_OPTIONS = OPTIONS_BY_CATEGORY["hold"]
WEAPON_OPTIONS = OPTIONS_BY_CATEGORY["weapon"]
SPECIAL_CREW_OPTIONS = OPTIONS_BY_CATEGORY["special_crew"]
UPGRADE_EFFECTS_BY_NAME = {
    str(row["name"]): row["stat_effects"] for row in UPGRADE_OPTIONS
}
ALL_OPTION_GROUPS = tuple(OPTIONS_BY_CATEGORY.values())


def test_every_build_designer_category_has_a_unique_catalog() -> None:
    validate_build_option_catalog(BUILD_ITEM_CATEGORIES, ALL_OPTION_GROUPS)


def test_sail_catalog_has_verified_calculator_effects_for_every_selectable_sail() -> None:
    validate_sail_seed_data(SAIL_OPTIONS)
    effects_by_name = {row["name"]: row["stat_effects"] for row in SAIL_OPTIONS}
    assert effects_by_name == {
        "Cheap Sails": {"speed_knots": 2},
        "Stitched Sails": {"speed_knots": 2.4},
        "Ultra-light Sails": {
            "speed_knots": 2.4,
            "cruising_maneuverability_pct": 15,
            "cruising_turn_speed_penalty_pct": -30,
        },
        "Storm Sails": {
            "speed_knots": 2.7,
            "strong_wind_cruising_speed_bonus_knots": 2.5,
        },
        "Elite Sails": {"speed_knots": 2.8},
        "Tacking Sails": {
            "speed_knots": 2.8,
            "turning_cruising_speed_bonus_knots": 2,
            "cruising_maneuverability_pct": -20,
        },
        "Reefed Sails": {
            "speed_knots": 2.9,
            "running_before_wind_speed_penalty_pct": -100,
            "broad_reach_cruising_speed_bonus_pct": -50,
        },
        "Tarpaulin Sails": {"speed_knots": 3.1, "maneuverability": -2},
        "Raiding Sails": {
            "speed_knots": 4.1,
            "cruising_maneuverability_pct": -20,
            "cruising_speed_gain_pct": -20,
        },
    }


def test_lantern_catalog_matches_verified_tooltip_values() -> None:
    validate_lantern_seed_data(LANTERN_OPTIONS)
    effects_by_name = {row["name"]: row["stat_effects"] for row in LANTERN_OPTIONS}
    assert effects_by_name == {
        "Blue Lantern": {"speed_pct": 6},
        "Bright Lantern": {"hold_capacity_pct": 12},
        "Golden Lantern": {"speed_pct": 5, "armor_pct": 5, "damage_pct": 5},
        "Green Lantern": {"hull_hp_pct": 7},
        "Ice Lantern": {"speed_pct": 5, "hold_capacity_pct": 5, "hull_hp_pct": 5},
        "Lilac Lantern": {"turn_rate_pct": 7},
        "Red Lantern": {"turn_rate_pct": 5, "damage_pct": 5, "exp_loot_pct": 7},
        "White Lantern": {"exp_loot_pct": 10},
        "Yellow Lantern": {"damage_pct": 7},
    }
    assert all(row["option_kind"] == "lantern" for row in LANTERN_OPTIONS)


def test_upgrade_catalog_matches_verified_in_game_panels() -> None:
    validate_upgrade_seed_data(UPGRADE_OPTIONS)
    names = {row["name"] for row in UPGRADE_OPTIONS}
    assert len(UPGRADE_OPTIONS) == 32
    assert {
        "Maneuverable Helm",
        "Small Hooks",
        "Repair Arsenal",
        "Fortified Ports",
        "Structural Expansion",
        "Reinforced Centre-Line",
        "Swivel Mortars",
    } <= names
    assert "Reinforced Ports" not in names
    assert all(str(row["option_kind"]).startswith("ship_upgrade_") for row in UPGRADE_OPTIONS)
    assert UPGRADE_EFFECTS_BY_NAME["Maneuverable Helm"] == {
        "turn_rate_pct": 8,
        "cruising_turn_speed_penalty_pct": -15,
    }
    assert UPGRADE_EFFECTS_BY_NAME["Double Hold"] == {
        "hold_capacity": 4500,
        "item_loss_pct": -40,
        "hull_hp_pct": -5,
    }
    assert UPGRADE_EFFECTS_BY_NAME["Repair Arsenal"] == {
        "durability": 150,
        "repair_item_efficiency_pct": 20,
    }
    assert UPGRADE_EFFECTS_BY_NAME["Lightweight Construction"] == {
        "mortar_reload_pct": 40,
        "hold_capacity_pct": 25,
        "mortar_damage_pct": -25,
    }


def test_specialist_catalog_matches_verified_screenshot_roster() -> None:
    validate_special_crew_seed_data(SPECIAL_CREW_OPTIONS)
    names = {str(row["name"]) for row in SPECIAL_CREW_OPTIONS}
    effects = {str(row["name"]): row["stat_effects"] for row in SPECIAL_CREW_OPTIONS}

    assert len(SPECIAL_CREW_OPTIONS) == 51
    assert names == {
        "Armorer", "Artillerist", "Boatman", "Bombardier", "Butcher",
        "Carpenter", "Clerk", "Commander", "Commodore", "Cook", "Corsair",
        "Daredevil", "Doctor", "Explorer", "First Mate", "Fisherman", "Ginger",
        "Gunner", "Harpooner", "Helmsman", "Junior provost", "Lifeguard",
        "Lucky One", "Master Gunner", "Mastman", "Midshipman", "Naval Cadet",
        "Navigator", "Old Hand", "Pilot", "Powder Monkey", "Provost", "Purser",
        "Quartermaster", "Recruiter", "Rigger", "Sail Handler", "Sailing Master",
        "Scout", "Scribe", "Seafarer", "Seeker", "Senior doctor", "Ship's Carpenter",
        "Skipper", "Steersman", "Sub-lieutenant", "Surgeon", "Swimmer", "Veteran",
        "Watchman",
    }
    assert effects["Doctor"] == {"boarding_company_shelling_survivability_pct": 40}
    assert effects["Sail Handler"] == {"speed_pct": 4}
    assert effects["First Mate"] == {"sail_deployment_speed_per_sailor_pct": 0.2}
    assert effects["Gunner"] == {"reload_pct": 4}
    assert effects["Artillerist"] == {"mortar_aiming_pct": 25}
    assert effects["Quartermaster"] == {"single_random_boarding_target_enabled": 1}
    assert effects["Swimmer"] == {"item_pickup_range_pct": 40}
    assert effects["Senior doctor"] == {"post_boarding_crew_healing_pct": 20}
    assert effects["Pilot"] == {"cruising_turn_speed_penalty_pct": -25}
    assert effects["Butcher"] == {"animal_slaughter_for_food_enabled": 1}
    assert effects["Carpenter"] == {"repair_speed_per_sailor_pct": 0.3}
    assert effects["Junior provost"] == {"large_fire_damage_pct": -50}
    assert effects["Provost"] == {"microfire_extinguishing_pct": 25}
    assert effects["Bombardier"] == {"loaded_weapons_mortar_reload_pct": 10}
    assert all(row["option_kind"] == "crew_specialist" for row in SPECIAL_CREW_OPTIONS)
    assert len({row["seed_id"] for row in SPECIAL_CREW_OPTIONS}) == 51
    assert all("Group:" in str(row.get("notes", "")) for row in SPECIAL_CREW_OPTIONS)


def test_hold_catalog_contains_tackles() -> None:
    assert "Tackles" in {str(row["name"]) for row in HOLD_OPTIONS}


def test_ammunition_catalog_contains_every_current_selectable_payload() -> None:
    names = {str(row["name"]) for row in AMMUNITION_OPTIONS}
    assert len(AMMUNITION_OPTIONS) == 16
    assert names == {
        "Bar Shots",
        "Burning Arrows",
        "Fire Ship",
        "Grapeshot",
        "Heated Shots",
        "Heavy Shots",
        "Large Phosphorous Mine",
        "Large Shrapnel Mines",
        "Phosphorous Shots",
        "Round Shots",
        "Saxon Shots",
        "Shrapnel Rounds",
        "Small Flaming Barrels",
        "Small Gunpowder Barrels",
        "Small Phosphorous Barrels",
        "Strike Rounds",
    }
    broadside_names = {
        "Round Shots",
        "Heated Shots",
        "Bar Shots",
        "Grapeshot",
        "Saxon Shots",
        "Heavy Shots",
    }
    assert broadside_names <= names
    assert len({row["seed_id"] for row in AMMUNITION_OPTIONS}) == 16


def test_every_seeded_numeric_effect_has_a_stat_catalog_definition() -> None:
    seeded_effect_keys = {
        key
        for rows in ALL_OPTION_GROUPS
        for row in rows
        for key in (row.get("stat_effects") or {})
    }
    calculated_effect_keys = {
        key
        for definition in STAT_DEFINITIONS
        for key in (
            definition.pct_effect,
            definition.flat_effect,
            definition.calculation_flat_effect,
        )
        if key
    }

    assert seeded_effect_keys <= calculated_effect_keys
