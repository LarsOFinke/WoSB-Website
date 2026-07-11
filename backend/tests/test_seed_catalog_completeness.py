from app.seeds.ammunition import AMMUNITION_OPTIONS
from app.seeds.build_catalog_quality import (
    validate_build_option_catalog,
    validate_lantern_seed_data,
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


def test_lantern_catalog_is_audited_and_selectable() -> None:
    validate_lantern_seed_data(LANTERN_OPTIONS)
    names = {row["name"] for row in LANTERN_OPTIONS}
    assert len(LANTERN_OPTIONS) >= 12
    assert {"Golden Lantern", "Ice Lantern", "Red Lantern", "Storm Lantern"} <= names
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
    assert all("prototype" not in str(row.get("notes", "")).casefold() for row in SPECIAL_CREW_OPTIONS)


def test_official_starter_templates_only_reference_current_upgrade_names() -> None:
    active_names = {str(row["name"]) for row in UPGRADE_OPTIONS}
    for build in STARTER_BUILD_DATA:
        for index in range(1, 7):
            name = build.get(f"upgrade_{index}")
            if name:
                assert name in active_names, f"{build['build_name']}: unknown upgrade {name}"

