from app.seeds.ammunition import AMMUNITION_OPTIONS
from app.seeds.build_catalog_quality import (
    validate_build_option_catalog,
    validate_lantern_seed_data,
    validate_sail_seed_data,
    validate_special_crew_seed_data,
    validate_upgrade_seed_data,
)
from app.seeds.categories import BUILD_ITEM_CATEGORIES
from app.seeds.consumables import CONSUMABLE_OPTIONS
from app.seeds.hold_items import HOLD_OPTIONS
from app.seeds.lanterns import LANTERN_OPTIONS
from app.seeds.sails import SAIL_OPTIONS
from app.seeds.special_crew import SPECIAL_CREW_OPTIONS
from app.seeds.upgrades import UPGRADE_EFFECTS_BY_NAME, UPGRADE_OPTIONS
from app.seeds.weapons import WEAPON_OPTIONS


ALL_OPTION_GROUPS = (
    SAIL_OPTIONS,
    UPGRADE_OPTIONS,
    LANTERN_OPTIONS,
    AMMUNITION_OPTIONS,
    CONSUMABLE_OPTIONS,
    HOLD_OPTIONS,
    WEAPON_OPTIONS,
    SPECIAL_CREW_OPTIONS,
)


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

    assert len(SPECIAL_CREW_OPTIONS) == 42
    assert {
        "Doctor", "Surgeon", "Sail Handler", "First Mate", "Master Gunner",
        "Ship's Carpenter", "Skipper", "Ginger", "Old Hand", "Artillerist",
    } <= names
    assert effects["Doctor"] == {"boarding_company_shelling_survivability_pct": 40}
    assert effects["Sail Handler"] == {"speed_pct": 4}
    assert effects["First Mate"] == {"speed_per_sailor_pct": 0.2}
    assert effects["Gunner"] == {"reload_pct": 4}
    assert effects["Artillerist"] == {"mortar_aiming_pct": 25}
    assert all(row["option_kind"] == "crew_specialist" for row in SPECIAL_CREW_OPTIONS)
    assert len({row["seed_id"] for row in SPECIAL_CREW_OPTIONS}) == 42
    assert all("Group:" in str(row.get("notes", "")) for row in SPECIAL_CREW_OPTIONS)


def test_hold_catalog_contains_tackles() -> None:
    assert "Tackles" in {str(row["name"]) for row in HOLD_OPTIONS}
