from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.modules.builds.services.build_stat_service import build_stat_rows, round_half_up
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_validation.errors import BuildValidationError
from app.modules.builds.services.build_validation.validator import BuildValidator
from app.modules.builds.services.stat_catalog import StatDefinition


CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "build-calculation-cases.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _definition(payload: dict[str, object]) -> StatDefinition:
    return StatDefinition(**payload)


def test_backend_matches_shared_build_calculation_contract(monkeypatch) -> None:
    from app.modules.builds.services import build_stat_service

    for case in CONTRACT["cases"]:
        definitions = tuple(_definition(row) for row in case["definitions"])
        monkeypatch.setattr(build_stat_service, "STAT_DEFINITIONS", definitions)
        rows = build_stat_rows(
            SimpleNamespace(**case["ship"]),
            case["effects"],
            effect_sets=case["effect_sets"],
        )
        by_key = {row["key"]: row for row in rows}
        for key, expected in case["expected"].items():
            actual = by_key[key]
            for field_name, expected_value in expected.items():
                assert actual[field_name] == expected_value, (
                    case["id"], key, field_name, actual[field_name], expected_value
                )


def test_calculation_contract_documents_the_zeven_raiding_sails_result() -> None:
    case = next(row for row in CONTRACT["cases"] if row["id"] == "de-zeven-raiding-sails")
    assert case["expected"]["speed_knots"]["effective"] == 14.7


def test_round_half_up_is_identical_for_positive_and_negative_ties() -> None:
    assert round_half_up(10.5) == 11
    assert round_half_up(-1.25, 1) == -1.3


def test_crew_validation_uses_the_same_half_up_rounding_as_stat_rows() -> None:
    ship = SimpleNamespace(
        crew_capacity=10,
        sailor_minimum=0,
        upgrade_effect_overrides=[],
        mortar_modification_effects=lambda _installed: {},
    )
    capacity_sails = SimpleNamespace(
        id=1,
        category=SimpleNamespace(key="sail"),
        stat_effects={"crew_capacity_pct": 5},
    )
    option_map = {("sail", "capacity sails"): capacity_sails}

    accepted = BuildCreate(
        build_name="Half-up capacity",
        ship_id=1,
        sails="Capacity Sails",
        sailors=11,
    )
    BuildValidator._validate_crew(ship, accepted, {}, [], option_map)

    rejected = accepted.model_copy(update={"sailors": 12})
    with pytest.raises(BuildValidationError, match=r"effective ship capacity \(11\)"):
        BuildValidator._validate_crew(ship, rejected, {}, [], option_map)
