"""Build Designer stat definitions and deterministic stat aggregation.

The Build Designer intentionally treats ship seed data as the base catalog and
upgrade effects as normalized modifiers. This keeps API responses explainable:
every shown stat can be traced back to a base ship field plus selected upgrade
modifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


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


STAT_DEFINITIONS: tuple[StatDefinition, ...] = (
    StatDefinition("durability", "Durability", "survivability", "durability", pct_effect="hull_hp_pct", precision=0),
    StatDefinition("speed_knots", "Speed", "mobility", "speed_knots", unit="kn", pct_effect="speed_pct", calculation_flat_effect="speed_knots", precision=1),
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
    StatDefinition("armor", "Broadside armor", "survivability", "armor", unit="%", pct_effect="armor_pct", precision=1),
    StatDefinition("hold_capacity", "Cargo hold", "logistics", "hold_capacity", unit="t", pct_effect="hold_capacity_pct", calculation_flat_effect="hold_capacity", precision=0),
    StatDefinition("hold_capacity_bonus", "Cargo hold bonus", "logistics", unit="t", flat_effect="hold_capacity", precision=0, source="upgrade_modifiers"),
    StatDefinition("crew_capacity", "Crew capacity", "crew", "crew_capacity", pct_effect="crew_capacity_pct", calculation_flat_effect="crew_capacity", precision=0),
    StatDefinition("crew_capacity_bonus", "Crew capacity bonus", "crew", flat_effect="crew_capacity", precision=0, source="upgrade_modifiers"),
    StatDefinition("sailor_minimum", "Sailor minimum", "crew", "sailor_minimum", flat_effect="sailor_minimum", precision=0, positive_is_good=False),
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
)

DEFINITION_BY_EFFECT_KEY: dict[str, StatDefinition] = {
    effect_key: definition
    for definition in STAT_DEFINITIONS
    for effect_key in (definition.pct_effect, definition.flat_effect)
    if effect_key
}


def stat_definitions_for_api() -> list[dict[str, Any]]:
    return [
        {
            "key": definition.key,
            "label": definition.label,
            "category": definition.category,
            "base_field": definition.base_field,
            "unit": definition.unit,
            "pct_effect": definition.pct_effect,
            "flat_effect": definition.flat_effect,
            "calculation_flat_effect": definition.calculation_flat_effect,
            "precision": definition.precision,
            "positive_is_good": definition.positive_is_good,
            "source": definition.source,
        }
        for definition in STAT_DEFINITIONS
    ]


def _get_number(source: object, field_name: str | None) -> float | None:
    if not field_name:
        return None
    value = getattr(source, field_name, None)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rounded(value: float | None, precision: int) -> int | float | None:
    if value is None:
        return None
    if precision <= 0:
        return int(round(value))
    return round(value, precision)


def _modifier(definition: StatDefinition, effects: Mapping[str, int | float]) -> float:
    total = 0.0
    if definition.pct_effect:
        total += float(effects.get(definition.pct_effect, 0) or 0)
    if definition.flat_effect:
        total += float(effects.get(definition.flat_effect, 0) or 0)
    return total


def _is_debuff(definition: StatDefinition, modifier: float) -> bool:
    if modifier == 0:
        return False
    return modifier < 0 if definition.positive_is_good else modifier > 0


def build_stat_rows(ship: object, effects: Mapping[str, int | float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    consumed_effects: set[str] = set()

    for definition in STAT_DEFINITIONS:
        base_value = _get_number(ship, definition.base_field)
        modifier = _modifier(definition, effects)
        if definition.pct_effect:
            consumed_effects.add(definition.pct_effect)
        if definition.flat_effect:
            consumed_effects.add(definition.flat_effect)

        if base_value is None and modifier == 0:
            continue

        effective_value: float | None = base_value
        if base_value is not None and definition.pct_effect:
            effective_value = base_value * (1 + float(effects.get(definition.pct_effect, 0) or 0) / 100)
        calculation_flat_effect = definition.calculation_flat_effect or definition.flat_effect
        if effective_value is not None and calculation_flat_effect:
            effective_value += float(effects.get(calculation_flat_effect, 0) or 0)
        if effective_value is None and definition.flat_effect:
            effective_value = modifier

        rows.append(
            {
                "key": definition.key,
                "label": definition.label,
                "category": definition.category,
                "base": _rounded(base_value, definition.precision),
                "modifier": _rounded(modifier, definition.precision),
                "effective": _rounded(effective_value, definition.precision),
                "unit": definition.unit,
                "precision": definition.precision,
                "modifier_kind": "percent" if definition.pct_effect and definition.base_field else "flat",
                "effect_key": definition.pct_effect or definition.flat_effect,
                "is_debuff": _is_debuff(definition, modifier),
                "source": definition.source,
            }
        )

    for key, raw_value in sorted(effects.items()):
        if key in consumed_effects:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if value == 0:
            continue
        rows.append(
            {
                "key": key,
                "label": key.replace("_pct", " %").replace("_", " ").title(),
                "category": "upgrade_modifiers",
                "base": None,
                "modifier": _rounded(value, 1 if not value.is_integer() else 0),
                "effective": _rounded(value, 1 if not value.is_integer() else 0),
                "unit": "%" if key.endswith("_pct") else None,
                "precision": 1 if not value.is_integer() else 0,
                "modifier_kind": "flat",
                "effect_key": key,
                "is_debuff": value < 0,
                "source": "upgrade_modifiers",
            }
        )

    return rows


def build_base_stats(ship: object) -> dict[str, int | float | str | None]:
    return {
        "durability": getattr(ship, "durability", 0),
        "speed_knots": getattr(ship, "speed_knots", 0),
        "maneuverability": getattr(ship, "maneuverability", 0),
        "armor": getattr(ship, "armor", 0),
        "hold_capacity": getattr(ship, "hold_capacity", 0),
        "crew_capacity": getattr(ship, "crew_capacity", 0),
        "sailor_minimum": getattr(ship, "sailor_minimum", 0),
        "weapon_layout": getattr(ship, "weapon_layout", None),
        "displacement_tons": getattr(ship, "displacement_tons", 0),
        "source": getattr(ship, "source", None),
    }


def effective_stats_from_rows(rows: list[dict[str, Any]]) -> dict[str, int | float | None]:
    return {str(row["key"]): row.get("effective") for row in rows}
