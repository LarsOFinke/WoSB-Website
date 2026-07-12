"""Composable ship seed catalog grouped by in-game rate."""

from app.seeds.ship_data.common import (
    SHIP_EVENT_SOURCE,
    SHIP_SCREENSHOT_AUDIT_DATE,
    SHIP_SCREENSHOT_SOURCE,
    SHIP_SOURCE_URL,
    SHIP_WEAPON_LAYOUT_AUDIT_DATE,
    SHIP_WIKI_SOURCE,
    ShipSeed,
    planning_sailor_minimum,
    ship,
)
from app.seeds.ship_data.rate_1 import RATE_1_SHIPS
from app.seeds.ship_data.rate_2 import RATE_2_SHIPS
from app.seeds.ship_data.rate_3 import RATE_3_SHIPS
from app.seeds.ship_data.rate_4 import RATE_4_SHIPS
from app.seeds.ship_data.rate_5 import RATE_5_SHIPS
from app.seeds.ship_data.rate_6 import RATE_6_SHIPS
from app.seeds.ship_data.rate_7 import RATE_7_SHIPS

SHIP_SEED_DATA: list[ShipSeed] = [
    *RATE_1_SHIPS,
    *RATE_2_SHIPS,
    *RATE_3_SHIPS,
    *RATE_4_SHIPS,
    *RATE_5_SHIPS,
    *RATE_6_SHIPS,
    *RATE_7_SHIPS,
]

__all__ = [
    "SHIP_EVENT_SOURCE",
    "SHIP_SCREENSHOT_AUDIT_DATE",
    "SHIP_SCREENSHOT_SOURCE",
    "SHIP_SEED_DATA",
    "SHIP_SOURCE_URL",
    "SHIP_WEAPON_LAYOUT_AUDIT_DATE",
    "SHIP_WIKI_SOURCE",
    "ShipSeed",
    "planning_sailor_minimum",
    "ship",
]
