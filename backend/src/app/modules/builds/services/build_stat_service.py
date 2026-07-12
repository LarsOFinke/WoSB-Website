"""Deterministic Build Designer stat aggregation.

Ship fields are the immutable base values; selected catalog effects are applied
by the small functions in this module. Stat metadata lives in ``stat_catalog``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Mapping

from app.modules.builds.services.stat_catalog import (
    STAT_DEFINITIONS,
    StatDefinition,
)

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
            "pct_base_field": definition.pct_base_field,
        }
        for definition in STAT_DEFINITIONS
    ]



def percentage_multiplier(
    effect_sets: Iterable[Mapping[str, int | float]] | None,
    effect_key: str,
    *,
    fallback_total: float = 0,
) -> float:
    """Combine percentage modifiers in the same order as the game.

    Separate installed items stack multiplicatively. ``fallback_total`` keeps
    backward compatibility for callers that only have an aggregated effect map.
    """

    values: list[float] = []
    if effect_sets is not None:
        for effect_set in effect_sets:
            value = float(effect_set.get(effect_key, 0) or 0)
            if value:
                values.append(value)
    if not values:
        return 1 + float(fallback_total or 0) / 100
    multiplier = 1.0
    for value in values:
        multiplier *= 1 + value / 100
    return multiplier


def apply_percentage_effects(
    base_value: float,
    effect_key: str,
    effect_sets: Iterable[Mapping[str, int | float]] | None,
    *,
    fallback_total: float = 0,
) -> float:
    return float(base_value) * percentage_multiplier(
        effect_sets, effect_key, fallback_total=fallback_total
    )

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


def build_stat_rows(
    ship: object,
    effects: Mapping[str, int | float],
    *,
    effect_sets: Iterable[Mapping[str, int | float]] | None = None,
) -> list[dict[str, Any]]:
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
            pct_base_value = (
                _get_number(ship, definition.pct_base_field)
                if definition.pct_base_field
                else base_value
            )
            if pct_base_value is None or (pct_base_value <= 0 < base_value):
                pct_base_value = base_value
            pct_delta = percentage_multiplier(
                effect_sets,
                definition.pct_effect,
                fallback_total=float(effects.get(definition.pct_effect, 0) or 0),
            ) - 1
            effective_value = base_value + (pct_base_value * pct_delta)
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
            "pct_base_field": definition.pct_base_field,
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
        "speed_min_knots": getattr(ship, "speed_min_knots", getattr(ship, "speed_knots", 0)),
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
