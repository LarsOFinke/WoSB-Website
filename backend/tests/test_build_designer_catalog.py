from contextlib import contextmanager

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_effect import BuildItemEffect
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_service import BuildValidationError, create_build
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.modules.squads.models.squad import Squad  # noqa: F401
from app.bootstrap.catalog_loader import load_master_data_catalog, load_ship_seed_document


SHIP_SEED_DATA = [
    row.model_dump(mode="json")
    for row in load_ship_seed_document().ships
]
WEAPON_OPTIONS = [
    row.model_dump(mode="json")
    for document in load_master_data_catalog().build_options
    if document.category == "weapon"
    for row in document.items
]


def _mounts(row: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(mount["slot_type"]): mount
        for mount in row["weapon_mounts"]
    }


def _legacy_weapon_layout(row: dict[str, object]) -> str:
    mounts = _mounts(row)
    layout = (
        f"{mounts['weapon_rear']['capacity']}-"
        f"{mounts['weapon_port']['capacity']}-"
        f"{mounts['weapon_front']['capacity']}"
    )
    mortar = mounts["weapon_mortar"]
    if int(mortar["capacity"]) > 0:
        caliber = float(mortar["max_caliber_inches"])
        rendered_caliber = int(caliber) if caliber.is_integer() else caliber
        layout += f" + mortar {rendered_caliber}in x{mortar['capacity']}"
    return layout


def _max_regular_weapon_class(row: dict[str, object]) -> str | None:
    return next(
        (
            str(mount["max_weapon_class"])
            for mount in row["weapon_mounts"]
            if mount.get("max_weapon_class")
        ),
        None,
    )


def _special_weapon_capacity(row: dict[str, object]) -> int:
    return sum(
        int(mount.get("special_weapon_capacity") or 0)
        for mount in row["weapon_mounts"]
    )




@contextmanager
def isolated_session():
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        yield db


EXPECTED_WEAPON_LAYOUTS = {'Firestorm': '12-28-1',
 'Ingermanland': '0-32-4',
 'Poltava': '0-23-4',
 'Surprise': '0-18-2',
 'Axel Thorsen': '0-0-0',
 'La Creole': '4-12-0',
 'Le Cerf': '0-9-0',
 'Savannah': '0-9-0',
 'Pickle': '0-6-0',
 'De Zeven Provincien': '4-42-4',
 'Sovereign': '4-38-8 + mortar 7in x2',
 'Victory': '4-49-4',
 'Neptuno': '4-36-4',
 'Sans Pareil': '4-38-2',
 'Anson': '4-30-2',
 'Le Saint Louis': '6-26-6',
 'Leopard': '0-25-4',
 'Essex': '2-21-2',
 'Red Arrow': '0-15-6 + mortar 7in x1',
 'Tie Long': '0-20-0',
 'Black Wind': '2-16-2',
 'Kwee Song': '0-10-10',
 'La Salamandre': '2-10-0',
 'Shunsen': '0-10-0',
 'Horizont': '2-8-0',
 'La Couronne': '8-28-0',
 'La Sirene': '4-32-0',
 'Mordaunt': '4-26-0',
 'Prins Willem': '6-26-4',
 'Falmouth': '4-18-0',
 'Flying Cloud': '0-16-0',
 'Friedrich Wilhelm': '4-21-4',
 'Three Hierarchs': '0-27-0',
 'Qing Long': '0-18-4',
 'Russia': '2-14-0',
 'Mercury': '2-9-0',
 'Friede': '2-7-0',
 '12 Apostolov': '0-59-0',
 'Santisima Trinidad': '4-63-0',
 'Redoutable': '0-43-0',
 'St. Pavel': '2-44-0',
 'Vasa': '4-31-2',
 'Montanes': '6-38-4',
 'Bonhomme Richard': '6-32-0',
 'Azov': '8-35-6',
 'Bellona': '0-35-0',
 'Constitution': '0-26-0',
 'San Martin': '0-20-0',
 'Phoenix': '0-12-0',
 'La Royale': '0-18-6 + mortar 11in x3',
 'Adventure': '4-19-0 + mortar 10in x2',
 'Kobukson': '0-15-0 + mortar 9in x4',
 'Shen': '0-22-1 + mortar 11in x2',
 'Iberia': '0-24-4',
 'San Juan Nepomuceno': '0-35-0',
 'Sparrow': '0-4-0 + mortar 8in x3',
 'Eagle': '4-8-0 + mortar 7in x2',
 'Le Requin': '2-12-0 + mortar 7in x1',
 'Golden Apostle': '0-7-0 + mortar 6in x1',
 'Polacca': '0-7-0 + mortar 6in x1',
 'Huracan': '0-85-2',
 'Octopus': '8-37-0',
 'Deadfish': '8-25-1',
 'Devourer': '12-11-8',
 'Black Prince': '2-15-2',
 'Balloon': '0-0-0',
 'Southampton': '2-15-0'}


SCREENSHOT_AUDITED_SHIPS = {'Pickle': (700, 9.2, 94, 1.6, 6000, 66, 900, 'light', '0-6-0'),
 'Horizont': (850, 8.4, 80, 3.2, 7000, 78, 1125, 'light', '2-8-0'),
 'Friede': (750, 8.8, 86, 2.2, 11000, 72, 1350, 'light', '2-7-0'),
 'Le Cerf': (900, 10.0, 97, 1.8, 8000, 78, 990, 'light', '0-9-0'),
 'La Salamandre': (1160, 8.8, 82, 3.6, 9500, 96, 1350, 'light', '2-10-0'),
 'Mercury': (1040, 9.2, 89, 2.5, 15500, 88, 2025, 'light', '2-9-0'),
 'Polacca': (980, 9.0, 102, 2.9, 9000, 74, 1575, 'light', '0-7-0 + mortar 6in x1'),
 'Phoenix': (1380, 8.2, 75, 4.5, 12500, 104, 1440, 'light', '0-12-0'),
 'Balloon': (200, 21.0, 50, 1.0, 1000, 8, 0, None, '0-0-0'),
 'Surprise': (1680, 10.5, 105, 2.4, 13000, 112, 2025, 'medium', '0-18-2'),
 'Essex': (2160, 8.9, 88, 4.8, 15500, 136, 2115, 'medium', '2-21-2'),
 'Falmouth': (1920, 9.4, 96, 3.3, 27500, 126, 3060, 'medium', '4-18-0'),
 'Constitution': (2560, 8.0, 68, 6.0, 21500, 148, 2565, 'medium', '0-26-0'),
 'Black Prince': (1700, 9.9, 90, 3.0, 14500, 120, 1800, 'light', '2-15-2'),
 'Devourer': (1760, 7.5, 110, 5.5, 17000, 144, 2610, 'medium', '12-11-8'),
 'Poltava': (2100, 9.6, 95, 2.8, 15500, 132, 2475, 'medium', '0-23-4'),
 'Anson': (2700, 8.2, 80, 5.6, 18500, 160, 3150, 'medium', '4-30-2'),
 'Mordaunt': (2380, 9.1, 87, 4.1, 34000, 148, 2475, 'medium', '4-26-0'),
 'Bellona': (3180, 7.5, 62, 7.0, 26000, 174, 3915, 'medium', '0-35-0'),
 'Kobukson': (2000, 8.0, 85, 4.6, 18000, 124, 2250, 'medium', '0-15-0 + mortar 9in x4'),
 'Deadfish': (3000, 6.6, 66, 8.0, 27000, 166, 4950, 'medium', '8-25-1'),
 'Ingermanland': (2340, 9.0, 87, 3.2, 17500, 152, 3060, 'heavy', '0-32-4'),
 'Sans Pareil': (3000, 7.7, 78, 6.4, 21500, 184, 3330, 'heavy', '4-38-2'),
 'La Sirene': (2660, 8.1, 80, 4.4, 43000, 170, 3600, 'heavy', '4-32-0'),
 'Redoutable': (3540, 7.0, 57, 8.0, 30500, 198, 3600, 'heavy', '0-43-0'),
 'Adventure': (2660, 8.2, 92, 5.2, 21000, 140, 2925, 'heavy', '4-19-0 + mortar 10in x2'),
 'Octopus': (2760, 8.3, 75, 6.8, 23000, 176, 3375, 'heavy', '8-37-0'),
 'Victory': (3740, 7.1, 66, 8.0, 25000, 204, 4050, 'heavy', '4-49-4'),
 'La Couronne': (3500, 7.6, 72, 5.5, 50000, 188, 4500, 'heavy', '8-28-0'),
 '12 Apostolov': (4400, 6.2, 49, 10.0, 36000, 220, 4500, 'heavy', '0-59-0'),
 'La Royale': (2900, 7.4, 83, 6.5, 24000, 156, 3870, 'heavy', '0-18-6 + mortar 11in x3'),
 'Huracan': (8000, 5.5, 42, 11.5, 54000, 288, 5625, 'heavy', '0-85-2'),
 'Savannah': (1000, 10.8, 92, 3.0, 10000, 94, 1575, 'light', '0-9-0'),
 'Golden Apostle': (900, 9.5, 120, 2.2, 8500, 96, 1260, 'light', '0-7-0 + mortar 6in x1'),
 'Shunsen': (1000, 8.5, 90, 3.0, 11000, 92, 1485, 'heavy', '0-10-0'),
 'Eagle': (1600, 9.4, 110, 2.2, 14000, 84, 1575, 'light', '4-8-0 + mortar 7in x2'),
 'Axel Thorsen': (880, 9.8, 110, 5.0, 7500, 66, 900, None, '0-0-0'),
 'Kwee Song': (1360, 7.9, 105, 4.5, 12500, 108, 1800, 'light', '0-10-10'),
 'Southampton': (1760, 9.7, 88, 3.2, 20500, 102, 1980, 'light', '2-15-0'),
 'Tie Long': (2310, 8.1, 68, 5.4, 18500, 130, 2610, 'light', '0-20-0'),
 'Red Arrow': (1940, 8.6, 95, 5.5, 18000, 140, 2700, 'medium', '0-15-6 + mortar 7in x1'),
 'Sparrow': (1000, 9.1, 95, 1.5, 10000, 72, 1350, 'medium', '0-4-0 + mortar 8in x3'),
 'Friedrich Wilhelm': (2020, 9.4, 96, 3.5, 26000, 120, 2700, 'medium', '4-21-4'),
 'Flying Cloud': (1800, 11.5, 58, 2.9, 30000, 100, 3375, 'medium', '0-16-0'),
 'Three Hierarchs': (2420, 8.4, 72, 5.6, 21000, 152, 2475, 'medium', '0-27-0'),
 'Qing Long': (1590, 10.8, 110, 2.1, 14000, 108, 1890, 'medium', '0-18-4'),
 'Prins Willem': (2440, 8.5, 78, 4.8, 45000, 170, 3150, 'medium', '6-26-4'),
 'Le Saint Louis': (2700, 7.9, 78, 5.6, 20000, 170, 2925, 'medium', '6-26-6'),
 'Azov': (2750, 7.7, 65, 6.4, 28000, 168, 3150, 'medium', '8-35-6'),
 'Shen': (2160, 7.9, 85, 5.2, 19000, 158, 2925, 'medium', '0-22-1 + mortar 11in x2'),
 'Iberia': (2220, 9.3, 92, 3.1, 16500, 140, 2565, 'medium', '0-24-4'),
 'San Juan Nepomuceno': (3020, 7.9, 70, 6.5, 24500, 180, 3690, 'medium', '0-35-0'),
 'Firestorm': (2600, 8.7, 85, 4.2, 20000, 170, 3150, 'heavy', '12-28-1'),
 'Neptuno': (2900, 8.2, 80, 5.8, 28000, 194, 4050, 'heavy', '4-36-4'),
 'Vasa': (4040, 6.6, 64, 7.5, 35000, 206, 3825, 'heavy', '4-31-2'),
 'St. Pavel': (3260, 7.3, 64, 7.3, 33500, 190, 4050, 'heavy', '2-44-0'),
 'Montanes': (2940, 7.5, 71, 7.2, 23500, 194, 3420, 'heavy', '6-38-4'),
 'Bonhomme Richard': (2800, 8.5, 74, 5.6, 39000, 180, 3330, 'heavy', '6-32-0'),
 'Santisima Trinidad': (4160, 6.4, 54, 9.0, 39500, 212, 4500, 'heavy', '4-63-0'),
 'De Zeven Provincien': (3320, 7.7, 75, 8.6, 26000, 188, 4440, 'heavy', '4-42-4'),
 'Sovereign': (3600, 7.4, 70, 7.0, 26500, 192, 4275, 'heavy', '4-38-8 + mortar 7in x2'),
 'Leopard': (2040, 9.6, 98, 3.0, 16500, 130, 2340, 'medium', '0-25-4'),
 'La Creole': (1400, 11.0, 100, 2.0, 11000, 96, 1620, 'light', '4-12-0'),
 'Black Wind': (1820, 9.4, 84, 4.0, 13000, 116, 2250, 'light', '2-16-2'),
 'Russia': (1600, 10.4, 91, 2.8, 22000, 108, 2070, 'light', '2-14-0'),
 'San Martin': (2140, 8.5, 72, 5.0, 17500, 126, 2475, 'light', '0-20-0'),
 'Le Requin': (1520, 9.6, 105, 3.2, 12500, 88, 2025, 'light', '2-12-0 + mortar 7in x1')}


SCREENSHOT_AUDITED_BUILD_DETAILS = {'Kobukson': (3, 'Phanokson', 5, 0),
 'Deadfish': (3, 'Ship', 5, 1),
 'Ingermanland': (2, 'Ship of the Line', 5, 0),
 'Sans Pareil': (2, 'Ship of the Line', 5, 0),
 'La Sirene': (2, 'Ship', 5, 0),
 'Redoutable': (2, 'Ship of the Line', 5, 0),
 'Adventure': (2, 'Galley', 5, 0),
 'Octopus': (2, 'Ship', 5, 1),
 'Victory': (1, 'Ship of the Line', 5, 0),
 'La Couronne': (1, 'Galleon', 6, 0),
 '12 Apostolov': (1, 'Ship of the Line', 5, 0),
 'La Royale': (1, 'Galley', 5, 0),
 'Huracan': (1, 'Ship of the Line', 6, 2),
 'Balloon': (6, 'Montgolfiere', 0, 0),
 'Savannah': (6, 'Frigate', 5, 0),
 'Golden Apostle': (6, 'Cutter', 5, 0),
 'Shunsen': (6, 'Junk', 5, 0),
 'Eagle': (5, 'Flute', 5, 0),
 'Axel Thorsen': (5, 'Schooner', 5, 1),
 'Kwee Song': (5, 'Phanokson', 5, 0),
 'Southampton': (5, 'Frigate', 5, 0),
 'Tie Long': (4, 'Atakebune', 5, 0),
 'Red Arrow': (4, 'Galleon', 5, 0),
 'Sparrow': (4, 'Tartane', 5, 0),
 'Friedrich Wilhelm': (4, 'Frigate', 5, 0),
 'Flying Cloud': (4, 'Clipper', 5, 0),
 'Three Hierarchs': (4, 'Ship of the Line', 5, 0),
 'Qing Long': (4, 'Junk', 5, 0),
 'Prins Willem': (3, 'Galleon', 6, 0),
 'Le Saint Louis': (3, 'Ship of the Line', 5, 0),
 'Azov': (3, 'Ship of the Line', 5, 0),
 'Shen': (3, 'Galiot', 5, 1),
 'Iberia': (3, 'Frigate', 5, 0),
 'San Juan Nepomuceno': (3, 'Ship of the Line', 5, 0),
 'Firestorm': (2, 'Frigate', 5, 1),
 'Neptuno': (2, 'Galleon', 5, 0),
 'Vasa': (2, 'Ship of the Line', 5, 0),
 'St. Pavel': (2, 'Ship of the Line', 5, 0),
 'Montanes': (2, 'Ship of the Line', 5, 0),
 'Bonhomme Richard': (2, 'Frigate', 5, 0),
 'Santisima Trinidad': (1, 'Ship of the Line', 5, 0),
 'De Zeven Provincien': (1, 'Ship of the Line', 5, 0),
 'Sovereign': (1, 'Galleon', 5, 0),
 'Leopard': (3, 'Ship of the Line', 5, 0)}


AUDITED_CRUISE_MAX_SPEEDS = {
    "12 Apostolov": 9.2,
    "Adventure": 11.0,
    "Anson": 11.0,
    "Azov": 10.6,
    "Balloon": 23.0,
    "Bellona": 10.5,
    "Black Prince": 12.2,
    "Constitution": 10.9,
    "De Zeven Provincien": 10.6,
    "Devourer": 10.5,
    "Eagle": 11.8,
    "Essex": 11.5,
    "Firestorm": 11.3,
    "Flying Cloud": 13.3,
    "Golden Apostle": 11.9,
    "Ingermanland": 11.6,
    "Huracan": 8.5,
    "Kobukson": 10.9,
    "La Couronne": 10.6,
    "La Royale": 10.4,
    "La Creole": 12.9,
    "La Sirene": 10.9,
    "Le Cerf": 12.2,
    "Mercury": 11.7,
    "Mordaunt": 11.6,
    "Neptuno": 11.0,
    "Poltava": 12.0,
    "Red Arrow": 11.3,
    "Redoutable": 10.0,
    "Russia": 12.5,
    "San Martin": 11.2,
    "Santisima Trinidad": 9.4,
    "Sans Pareil": 10.6,
    "Savannah": 12.8,
    "Shunsen": 11.2,
    "Sovereign": 10.4,
    "Vasa": 9.6,
    "Victory": 10.1,
}


def test_shipyard_speed_ranges_match_owned_ship_screenshots() -> None:
    rows = {row["name"]: row for row in SHIP_SEED_DATA}
    assert rows["La Couronne"]["speed_min_knots"] == 7.6
    assert rows["La Couronne"]["speed_knots"] == 10.6
    assert rows["La Creole"]["speed_min_knots"] == 11.0
    assert rows["La Creole"]["speed_knots"] == 12.9
    assert rows["Mordaunt"]["speed_min_knots"] == 9.1
    assert rows["Russia"]["speed_min_knots"] == 10.4
    assert rows["12 Apostolov"]["speed_knots"] == 9.2
    assert rows["Balloon"]["speed_knots"] == 23.0
    assert rows["Flying Cloud"]["speed_knots"] == 13.3
    assert rows["Huracan"]["speed_knots"] == 8.5
    assert rows["La Royale"]["speed_knots"] == 10.4
    assert rows["Azov"]["speed_knots"] == 10.6
    assert rows["Firestorm"]["speed_knots"] == 11.3
    assert rows["Santisima Trinidad"]["speed_knots"] == 9.4
    assert rows["Savannah"]["speed_knots"] == 12.8
    assert rows["Sovereign"]["speed_knots"] == 10.4


def test_in_game_screenshot_ship_stats_match_catalog() -> None:
    rows = {row["name"]: row for row in SHIP_SEED_DATA}
    assert set(rows) == set(SCREENSHOT_AUDITED_SHIPS)
    for name, expected in SCREENSHOT_AUDITED_SHIPS.items():
        row = rows[name]
        actual = (
            row["durability"],
            row["speed_min_knots"],
            row["maneuverability"],
            row["armor"],
            row["hold_capacity"],
            row["crew_capacity"],
            row["displacement_tons"],
            _max_regular_weapon_class(row),
            _legacy_weapon_layout(row),
        )
        assert actual == expected, name
        assert row["speed_knots"] == AUDITED_CRUISE_MAX_SPEEDS.get(name, expected[1])
        assert row["source"].startswith("WoSB in-game")


def test_in_game_screenshot_build_designer_metadata_match_catalog() -> None:
    rows = {row["name"]: row for row in SHIP_SEED_DATA}
    for name, expected in SCREENSHOT_AUDITED_BUILD_DETAILS.items():
        row = rows[name]
        actual = (
            row["rate"],
            row["ship_type"],
            row["upgrade_slots"],
            _special_weapon_capacity(row),
        )
        assert actual == expected, name


def test_all_ship_weapon_layouts_match_audited_catalog() -> None:
    actual = {row["name"]: _legacy_weapon_layout(row) for row in SHIP_SEED_DATA}
    assert actual == EXPECTED_WEAPON_LAYOUTS
    zeven = next(row for row in SHIP_SEED_DATA if row["name"] == "De Zeven Provincien")
    mounts = _mounts(zeven)
    assert mounts["weapon_front"]["capacity"] == 4
    assert mounts["weapon_port"]["capacity"] == 42
    assert mounts["weapon_rear"]["capacity"] == 4


def test_duplicate_upgrades_are_rejected_server_side() -> None:
    with isolated_session() as db:
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "upgrade"))
        if category is None:
            category = BuildItemCategory(key="upgrade", label="Upgrades", sort_order=10, is_active=True)
            db.add(category)
            db.flush()
        option = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Duplicate Test Upgrade",
            )
        )
        if option is None:
            option = BuildItemOption(
                category_id=category.id,
                name="Duplicate Test Upgrade",
                sort_order=10,
                is_active=True,
            )
            db.add(option)
        ship = db.scalar(select(Ship).where(Ship.name == "Duplicate Upgrade Test Ship"))
        if ship is None:
            ship = Ship(
                name="Duplicate Upgrade Test Ship",
                rate=5,
                ship_type="Test",
                durability=100,
                speed_knots=8,
                maneuverability=80,
                armor=1,
                hold_capacity=100,
                crew_capacity=20,
                sailor_minimum=0,
                displacement_tons=100,
                source="test",
                sail_slots=1,
                upgrade_slots=5,
                has_lantern=True,
            )
            db.add(ship)
        db.commit()
        try:
            create_build(
                db,
                BuildCreate(
                    build_name="Duplicate upgrades",
                    ship_id=ship.id,
                    upgrade_1="Duplicate Test Upgrade",
                    upgrade_2="Duplicate Test Upgrade",
                ),
            )
        except BuildValidationError as exc:
            assert "each upgrade can only be selected once" in str(exc)
        else:
            raise AssertionError("Duplicate upgrades must be rejected.")


def test_all_ship_seeds_use_current_panel_or_event_provenance() -> None:
    assert len(SHIP_SEED_DATA) == 67
    allowed_sources = {
        "WoSB in-game shipyard screenshot audit 2026-07",
        "WoSB in-game current-event tooltip screenshot audit 2026-07",
        "WoSB in-game owned-ship screenshot audit 2026-07-28",
        "WoSB in-game owned-ship screenshot audit 2026-07-29",
    }
    assert {str(row["source"]) for row in SHIP_SEED_DATA} <= allowed_sources


def test_weapon_catalog_uses_dedicated_ship_arcs() -> None:
    expected = {
        "cannon": {"weapon_port", "weapon_starboard"},
        "bow_stern": {"weapon_front", "weapon_rear"},
        "mortar": {"weapon_mortar"},
        "mortar_launcher": {"weapon_mortar"},
        "special_weapon": {"weapon_front", "weapon_rear", "weapon_special"},
    }
    assert WEAPON_OPTIONS
    for row in WEAPON_OPTIONS:
        slots = set(row["allowed_slot_types"])
        assert slots == expected[row["option_kind"]], row["name"]
        if row["option_kind"] == "cannon":
            assert row["weapon_class"] in {"light", "medium", "heavy"}
        else:
            assert row["weapon_class"] is None


def test_specialist_effects_apply_once_even_when_quantity_is_submitted() -> None:
    with isolated_session() as db:
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "special_crew"))
        if category is None:
            category = BuildItemCategory(
                key="special_crew", label="Specialists", sort_order=20, is_active=True
            )
            db.add(category)
            db.flush()
        option = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Capacity Test Specialist",
            )
        )
        if option is None:
            option = BuildItemOption(
                category_id=category.id,
                name="Capacity Test Specialist",
                sort_order=10,
                is_active=True,
            )
            option.effects = [BuildItemEffect(effect_key="crew_capacity", effect_value=3)]
            db.add(option)
        ship = db.scalar(select(Ship).where(Ship.name == "Specialist Quantity Test Ship"))
        if ship is None:
            ship = Ship(
                name="Specialist Quantity Test Ship",
                rate=5,
                ship_type="Test",
                durability=100,
                speed_knots=8,
                maneuverability=80,
                armor=1,
                hold_capacity=100,
                crew_capacity=20,
                sailor_minimum=10,
                displacement_tons=100,
                source="test",
                sail_slots=1,
                upgrade_slots=4,
                has_lantern=True,
            )
            db.add(ship)
        db.commit()

        build = create_build(
            db,
            BuildCreate(
                build_name="Weighted specialists",
                ship_id=ship.id,
                sailors=20,
                soldiers=3,
                special_crew_slots=[{"item": "Capacity Test Specialist", "quantity": 2}],
            ),
        )
        assert build.ship_stats["crew_capacity"] == 23
        assert build.ship_stats["special_crew_effects"]["crew_capacity"] == 3
        assert build.special_crew_slots == [{"item": "Capacity Test Specialist", "quantity": 1}]
        assert build.ship_stats["crew_remaining"] == 0


def test_json_mounts_keep_stern_broadside_bow_game_order_explicit() -> None:
    rows = {row["name"]: row for row in SHIP_SEED_DATA}
    couronne_mounts = _mounts(rows["La Couronne"])
    assert couronne_mounts["weapon_rear"]["capacity"] == 8
    assert couronne_mounts["weapon_front"]["capacity"] == 0
    poltava_mounts = _mounts(rows["Poltava"])
    assert poltava_mounts["weapon_rear"]["capacity"] == 0
    assert poltava_mounts["weapon_front"]["capacity"] == 4
