"""Ship catalog seed data for the Build Designer.

The executable catalog is grouped by in-game rate in :mod:`app.seeds.ship_data`.
Every entry is built through a typed factory so shared defaults, provenance, and
the documented sailor-planning rule remain consistent.

``weapon_layout`` always means ``bow-side-stern`` plus an optional
``mortar Xin xN`` suffix. ``max_weapon_class`` stores the explicit audited
Light/Medium/Heavy mount ceiling instead of a pound-value heuristic.

Only Build Designer data is represented. Player inventory/progress, construction
costs, port restrictions, hull dimensions, swivel guns, integrity and flavor
traits intentionally remain outside this catalog.
"""

from app.seeds.ship_data import (
    SHIP_EVENT_SOURCE,
    SHIP_SCREENSHOT_AUDIT_DATE,
    SHIP_SCREENSHOT_SOURCE,
    SHIP_SEED_DATA,
    SHIP_SOURCE_URL,
    SHIP_WEAPON_LAYOUT_AUDIT_DATE,
    SHIP_WIKI_SOURCE,
)

__all__ = [
    "SHIP_EVENT_SOURCE",
    "SHIP_SCREENSHOT_AUDIT_DATE",
    "SHIP_SCREENSHOT_SOURCE",
    "SHIP_SEED_DATA",
    "SHIP_SOURCE_URL",
    "SHIP_WEAPON_LAYOUT_AUDIT_DATE",
    "SHIP_WIKI_SOURCE",
]
