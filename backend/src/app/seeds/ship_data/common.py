"""Typed factory and provenance constants for Build Designer ship seeds."""

from __future__ import annotations

from typing import Literal, TypeAlias

WeaponClass: TypeAlias = Literal["light", "medium", "heavy"]
ShipSeed: TypeAlias = dict[str, object]

SHIP_SOURCE_URL = "https://world-of-sea-battle.fandom.com/wiki/Ships"
SHIP_WEAPON_LAYOUT_AUDIT_DATE = "2026-07-12"
SHIP_SCREENSHOT_AUDIT_DATE = "2026-07-12"
SHIP_WIKI_SOURCE = "WoSB wiki ship page audit 2026-07"
SHIP_SCREENSHOT_SOURCE = "WoSB in-game shipyard screenshot audit 2026-07"
SHIP_EVENT_SOURCE = "WoSB in-game current-event tooltip screenshot audit 2026-07"

# The shipyard panel exposes a speed range. The left endpoint is the ship's
# base/cruising speed; the right endpoint is its cruise maximum. Percentage
# speed effects modify the base speed and shift the cruise maximum by the same
# absolute delta. Flat sail bonuses labelled "Cruise max. speed" apply only to
# the maximum endpoint.


def planning_sailor_minimum(crew_capacity: int) -> int:
    """Return the current planning target when no official minimum is known.

    The game panels supplied for this catalog do not expose minimum sailing crew.
    The Build Designer therefore uses a documented 40% planning rule, rounded to
    the nearest whole sailor. Individual ships may override this when an audited
    value is available.
    """

    return int(crew_capacity * 0.4 + 0.5)


def ship(
    *,
    name: str,
    rate: int,
    ship_type: str,
    durability: int,
    speed_raw: float,
    cruise_max_speed_knots: float | None = None,
    maneuverability: float,
    armor: float,
    hold_capacity: int,
    crew_capacity: int,
    displacement_tons: int,
    max_weapon_class: WeaponClass | None,
    weapon_layout: str,
    source: str = SHIP_SCREENSHOT_SOURCE,
    sailor_minimum: int | None = None,
    sail_slots: int = 1,
    upgrade_slots: int = 5,
    has_lantern: bool = True,
    special_weapon_capacity: int = 0,
    seed_id: str | None = None,
    image_url: str | None = None,
) -> ShipSeed:
    """Create one canonical seed payload with explicit Build Designer fields.

    ``speed_raw`` is the left endpoint shown by the shipyard speed range.
    ``cruise_max_speed_knots`` is the right endpoint. When no audited maximum is
    available yet, the maximum safely falls back to the base speed instead of
    inventing a conversion factor.
    """

    row: ShipSeed = {
        "name": name,
        "rate": rate,
        "ship_type": ship_type,
        "durability": durability,
        "speed_min_knots": float(speed_raw),
        "speed_knots": float(
            cruise_max_speed_knots
            if cruise_max_speed_knots is not None
            else speed_raw
        ),
        "maneuverability": maneuverability,
        "armor": armor,
        "hold_capacity": hold_capacity,
        "crew_capacity": crew_capacity,
        "sailor_minimum": (
            planning_sailor_minimum(crew_capacity)
            if sailor_minimum is None
            else sailor_minimum
        ),
        "displacement_tons": displacement_tons,
        "source": source,
        "sail_slots": sail_slots,
        "upgrade_slots": upgrade_slots,
        "has_lantern": has_lantern,
        "max_weapon_class": max_weapon_class,
        "weapon_layout": weapon_layout,
    }
    if special_weapon_capacity:
        row["special_weapon_capacity"] = special_weapon_capacity
    if seed_id:
        row["seed_id"] = seed_id
    if image_url:
        row["image_url"] = image_url
    return row
