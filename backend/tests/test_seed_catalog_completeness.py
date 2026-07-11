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
from app.seeds.starter_content import STARTER_BUILD_DATA
from app.seeds.hold_items import HOLD_OPTIONS
from app.seeds.lanterns import LANTERN_OPTIONS
from app.seeds.sails import SAIL_OPTIONS
from app.seeds.special_crew import SPECIAL_CREW_OPTIONS
from app.seeds.upgrades import UPGRADE_OPTIONS
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
        "Lilac Lantern": {"turn_rate_pct": 7},
        "Red Lantern": {"turn_rate_pct": 5, "damage_pct": 5, "exp_loot_pct": 7},
        "White Lantern": {"exp_loot_pct": 10},
        "Yellow Lantern": {"damage_pct": 7},
    }
    assert all(row["option_kind"] == "lantern" for row in LANTERN_OPTIONS)


def test_upgrade_catalog_uses_current_names_and_effect_metadata() -> None:
    validate_upgrade_seed_data(UPGRADE_OPTIONS)
    names = {row["name"] for row in UPGRADE_OPTIONS}
    assert len(UPGRADE_OPTIONS) >= 30
    assert {"Reinforced Ports", "Emergency Powder Charge", "Structural Expansion"} <= names
    assert "Fortified Ports" not in names
    assert all(row["option_kind"] == "ship_upgrade" for row in UPGRADE_OPTIONS)


def test_specialist_catalog_replaces_placeholder_special_crew_rows() -> None:
    validate_special_crew_seed_data(SPECIAL_CREW_OPTIONS)
    names = {row["name"] for row in SPECIAL_CREW_OPTIONS}
    assert len(SPECIAL_CREW_OPTIONS) == 24
    assert {"Artillerist", "Boarding Master", "Carpenter", "Navigator", "Surgeon"} <= names
    assert all(row["option_kind"] == "crew_specialist" for row in SPECIAL_CREW_OPTIONS)
    assert len({row["seed_id"] for row in SPECIAL_CREW_OPTIONS}) == 24
    assert all(
        "prototype" not in str(row.get("notes", "")).casefold() for row in SPECIAL_CREW_OPTIONS
    )


def test_official_starter_templates_only_reference_current_upgrade_names() -> None:
    active_names = {str(row["name"]) for row in UPGRADE_OPTIONS}
    for build in STARTER_BUILD_DATA:
        for index in range(1, 7):
            name = build.get(f"upgrade_{index}")
            if name:
                assert name in active_names, f"{build['build_name']}: unknown upgrade {name}"


def test_official_starter_templates_reference_active_equipment_catalog() -> None:
    active_sails = {str(row["name"]) for row in SAIL_OPTIONS}
    active_lanterns = {str(row["name"]) for row in LANTERN_OPTIONS}
    for build in STARTER_BUILD_DATA:
        assert build.get("sails") in active_sails
        assert build.get("lantern") in active_lanterns
