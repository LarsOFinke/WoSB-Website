"""Resolve global upgrade effects with optional ship-specific values."""

from __future__ import annotations

from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.ships.models.ship import Ship


def ship_upgrade_override_values(ship: Ship, option_id: int) -> dict[str, int | float]:
    return {
        row.effect_key: row.normalized_value
        for row in ship.upgrade_effect_overrides
        if row.option_id == option_id
    }


def effective_upgrade_effects(
    option: BuildItemOption,
    ship: Ship | None,
) -> dict[str, int | float]:
    """Return the effective effect map for an upgrade on one ship.

    Non-upgrade options and calls without a ship keep their catalog values.
    Ship values are a sparse overlay, so new global effect keys remain inherited
    unless an administrator explicitly overrides them for that ship.
    """

    effects = dict(option.stat_effects)
    if ship is None or option.category.key != "upgrade":
        return effects
    effects.update(ship_upgrade_override_values(ship, option.id))
    return effects


def has_ship_upgrade_override(option: BuildItemOption, ship: Ship | None) -> bool:
    return bool(ship and any(row.option_id == option.id for row in ship.upgrade_effect_overrides))
