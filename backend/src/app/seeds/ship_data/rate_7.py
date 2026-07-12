"""Rate 7 ship seeds."""

from app.seeds.ship_data.common import (
    SHIP_SCREENSHOT_SOURCE,
    ship,
)

RATE_7_SHIPS = [
    ship(
        name='Friede',
        rate=7,
        ship_type='Flute',
        durability=750,
        speed_raw=8.8,
        maneuverability=86,
        armor=2.2,
        hold_capacity=11000,
        crew_capacity=72,
        displacement_tons=1350,
        max_weapon_class='light',
        weapon_layout='2-7-0',
        source=SHIP_SCREENSHOT_SOURCE,
    ),
    ship(
        name='Horizont',
        rate=7,
        ship_type='Brigantine',
        durability=850,
        speed_raw=8.4,
        maneuverability=80,
        armor=3.2,
        hold_capacity=7000,
        crew_capacity=78,
        displacement_tons=1125,
        max_weapon_class='light',
        weapon_layout='2-8-0',
        source=SHIP_SCREENSHOT_SOURCE,
    ),
    ship(
        name='Pickle',
        rate=7,
        ship_type='Schooner',
        durability=700,
        speed_raw=9.2,
        maneuverability=94,
        armor=1.6,
        hold_capacity=6000,
        crew_capacity=66,
        displacement_tons=900,
        max_weapon_class='light',
        weapon_layout='0-6-0',
        source=SHIP_SCREENSHOT_SOURCE,
    ),
]
