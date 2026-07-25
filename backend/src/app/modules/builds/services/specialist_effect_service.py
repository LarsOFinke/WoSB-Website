"""Resolve Specialist effects against a build's crew allocation.

Catalog rows store the literal tooltip modifier. Effects such as ``+0.2% per
Sailor`` must be expanded with the current crew allocation, while conditional
or boolean abilities must stay separate from always-on ship base modifiers.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping


PER_CREW_EFFECTS: dict[str, tuple[str, str]] = {
    "speed_per_sailor_pct": ("speed_pct", "sailors"),
    "item_reload_per_sailor_pct": ("item_reload_pct", "sailors"),
    "ammo_switch_per_sailor_pct": ("ammo_switch_speed_pct", "sailors"),
    "low_durability_reload_per_sailor_pct": ("low_durability_reload_pct", "sailors"),
    "boarding_cargo_weight_per_boarder_pct": ("boarding_cargo_weight_pct", "boarders"),
    "fishing_catch_per_boarder_pct": ("fishing_catch_pct", "boarders"),
    "fishing_speed_per_sailor_pct": ("fishing_speed_pct", "sailors"),
    "repair_speed_per_sailor_pct": ("repair_speed_pct", "sailors"),
}


def _crew_counts(*, sailors: int, soldiers: int, musketeers: int, mercenaries: int) -> dict[str, int]:
    normalized = {
        "sailors": max(0, int(sailors or 0)),
        "soldiers": max(0, int(soldiers or 0)),
        "musketeers": max(0, int(musketeers or 0)),
        "mercenaries": max(0, int(mercenaries or 0)),
    }
    normalized["boarders"] = (
        normalized["soldiers"] + normalized["musketeers"] + normalized["mercenaries"]
    )
    return normalized


def resolve_specialist_effects(
    weighted_effects: Iterable[tuple[Mapping[str, int | float], int]],
    *,
    sailors: int,
    soldiers: int,
    musketeers: int,
    mercenaries: int,
) -> dict[str, int | float]:
    """Return effective Specialist modifiers for one build.

    ``weighted_effects`` keeps the historical tuple shape for API compatibility.
    Every Specialist type is unique and therefore contributes exactly once.
    Boolean ``*_enabled`` effects are idempotent.
    """

    counts = _crew_counts(
        sailors=sailors,
        soldiers=soldiers,
        musketeers=musketeers,
        mercenaries=mercenaries,
    )
    totals: dict[str, int | float] = {}

    for effects, _raw_quantity in weighted_effects:
        quantity = 1
        for key, raw_value in effects.items():
            value = float(raw_value or 0)
            if value == 0:
                continue

            dynamic = PER_CREW_EFFECTS.get(key)
            if dynamic is not None:
                target_key, count_key = dynamic
                totals[target_key] = totals.get(target_key, 0) + (
                    value * counts[count_key] * quantity
                )
                continue

            if key.endswith("_enabled"):
                totals[key] = 1
                continue

            totals[key] = totals.get(key, 0) + (value * quantity)

    return {
        key: int(value) if float(value).is_integer() else round(float(value), 4)
        for key, value in totals.items()
    }
