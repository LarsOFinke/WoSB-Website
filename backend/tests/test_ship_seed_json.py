import json

import pytest

from app.bootstrap.catalog_loader import (
    EXPECTED_WEAPON_SLOT_CODES,
    MASTER_DATA_MANIFEST_PATH,
    SHIP_SEED_PATH,
    load_master_data_catalog,
    load_ship_rate_document,
    load_ship_seed_document,
)


def _mounts(ship) -> dict[str, object]:
    return {mount.slot_type: mount for mount in ship.weapon_mounts}


def test_ship_seed_catalog_lives_at_backend_root_and_uses_explicit_mounts() -> None:
    document = load_ship_seed_document()

    assert SHIP_SEED_PATH.name == "ships"
    assert SHIP_SEED_PATH.parent.name == "seeds"
    assert SHIP_SEED_PATH.parent.parent.name == "backend"
    assert MASTER_DATA_MANIFEST_PATH.is_file()
    assert len(document.ships) == 67
    assert all(
        {mount.slot_type for mount in ship.weapon_mounts}
        == EXPECTED_WEAPON_SLOT_CODES
        for ship in document.ships
    )


def test_positional_special_and_mortar_capabilities_are_seeded_explicitly() -> None:
    ships = {ship.name: ship for ship in load_ship_seed_document().ships}

    huracan = _mounts(ships["Huracan"])
    assert huracan["weapon_front"].capacity == 2
    assert huracan["weapon_front"].special_weapon_capacity == 2

    octopus = _mounts(ships["Octopus"])
    assert octopus["weapon_rear"].capacity == 8
    assert octopus["weapon_rear"].special_weapon_capacity == 1

    axel = _mounts(ships["Axel Thorsen"])
    assert axel["weapon_special"].capacity == 1
    assert axel["weapon_special"].special_weapon_capacity == 1

    sovereign = _mounts(ships["Sovereign"])
    assert sovereign["weapon_mortar"].capacity == 2
    assert sovereign["weapon_mortar"].max_caliber_inches == 7


def test_permanent_mortar_modifications_are_explicit_and_ship_specific() -> None:
    ships = {ship.name: ship for ship in load_ship_seed_document().ships}
    supported = {
        ship.name
        for ship in ships.values()
        if ship.mortar_modification is not None
    }

    assert supported == {"Black Wind", "Falmouth", "Friede"}

    black_wind = ships["Black Wind"].mortar_modification
    assert black_wind is not None
    assert black_wind.mortar_capacity == 1
    assert black_wind.max_caliber_inches == 7
    assert black_wind.broadside_capacity_delta == -5
    assert black_wind.durability_delta == -180
    assert black_wind.crew_capacity_delta == -23

    falmouth = ships["Falmouth"].mortar_modification
    assert falmouth is not None
    assert falmouth.mortar_capacity == 2
    assert falmouth.broadside_capacity_delta == -5

    friede = ships["Friede"].mortar_modification
    assert friede is not None
    assert friede.mortar_capacity == 1
    assert friede.broadside_capacity_delta == -2


def test_owned_ship_upgrade_overrides_are_sparse_and_rate_specific() -> None:
    ships = {ship.name: ship for ship in load_ship_seed_document().ships}
    overridden = {
        ship.name for ship in ships.values() if ship.upgrade_effect_overrides
    }
    assert overridden == {
        "Adventure",
        "Azov",
        "Black Prince",
        "De Zeven Provincien",
        "Eagle",
        "Firestorm",
        "Golden Apostle",
        "Ingermanland",
        "La Couronne",
        "La Creole",
        "La Sirene",
        "Le Cerf",
        "Mercury",
        "Neptuno",
        "Redoutable",
        "Russia",
        "San Martin",
        "Santisima Trinidad",
        "Sans Pareil",
        "Savannah",
        "Shunsen",
        "Sovereign",
        "Vasa",
        "Victory",
    }

    def values(ship_name: str, upgrade_seed_id: str) -> dict[str, int | float]:
        return next(
            row.stat_effects
            for row in ships[ship_name].upgrade_effect_overrides
            if row.upgrade_seed_id == upgrade_seed_id
        )

    assert values("Adventure", "reinforced-masts") == {
        "speed_knots": 0.4,
        "sail_efficiency": 0.8,
    }
    assert values("Adventure", "teak-frames") == {
        "armor": 1.0,
        "crew_capacity": 14,
    }
    assert ships["Anson"].upgrade_effect_overrides == []
    assert values("Black Prince", "reinforced-masts") == {
        "speed_knots": 0.6,
        "sail_efficiency": 1.2,
    }
    assert values("Black Prince", "teak-frames") == {
        "armor": 2.0,
        "crew_capacity": 6,
    }
    assert values("Azov", "ammunition-cradles") == {"reload_pct": 18}
    assert values("Azov", "reinforced-cannons") == {
        "bow_stern_weapon_damage_pct": 61,
    }
    assert values("Firestorm", "reinforced-cannons") == {
        "bow_stern_weapon_damage_pct": 35,
    }
    assert values("Santisima Trinidad", "ammunition-cradles") == {
        "reload_pct": 18,
    }
    assert values("Savannah", "reinforced-cannons") == {
        "bow_stern_weapon_damage_pct": 121,
    }
    assert values("Sovereign", "reinforced-cannons") == {
        "bow_stern_weapon_damage_pct": 61,
    }


def test_owned_ship_screenshot_batch_has_audited_source_and_expected_size() -> None:
    owned = {
        "Adventure", "Anson", "Azov", "Bellona", "Black Prince", "Constitution",
        "De Zeven Provincien", "Devourer", "Eagle", "Essex", "Firestorm",
        "Golden Apostle", "Ingermanland", "Kobukson", "La Couronne", "La Creole",
        "La Sirene", "Le Cerf", "Mercury", "Mordaunt", "Neptuno", "Poltava",
        "Red Arrow", "Redoutable", "Russia", "San Martin", "Santisima Trinidad",
        "Sans Pareil", "Savannah", "Shunsen", "Sovereign", "Vasa", "Victory",
    }
    ships = {ship.name: ship for ship in load_ship_seed_document().ships}
    assert len(owned) == 33
    assert owned <= set(ships)
    assert {ships[name].source for name in owned} == {
        "WoSB in-game owned-ship screenshot audit 2026-07-28"
    }


def test_ship_seed_loader_rejects_special_capacity_above_mount_capacity(tmp_path) -> None:
    source_path = SHIP_SEED_PATH / "rates" / "rate-1.json"
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    payload["items"][0]["weapon_mounts"][0]["capacity"] = 1
    payload["items"][0]["weapon_mounts"][0]["special_weapon_capacity"] = 2
    invalid_path = tmp_path / "rate-1.json"
    invalid_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeError, match="special_weapon_capacity"):
        load_ship_rate_document(invalid_path)


def test_manifest_covers_every_json_master_data_file() -> None:
    catalog = load_master_data_catalog()

    assert catalog.manifest.catalog == "wosb-master-data"
    assert len(catalog.manifest.documents) == 20
    assert {document.category for document in catalog.build_options} == {
        "sail",
        "upgrade",
        "lantern",
        "ammunition",
        "consumable",
        "hold",
        "weapon",
        "special_crew",
    }
