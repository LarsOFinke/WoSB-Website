"""Specialist catalog for the Build Designer.

World of Sea Battle B20 renamed special crew to Specialists and introduced the
unlock/search flow. The database key remains ``special_crew`` for backwards
compatibility with saved builds and API payloads.
"""

SPECIALIST_CATALOG_REVISION = "B20-fleet-audit-2026-07"


def _specialist(name: str, effects: dict[str, int | float], notes: str) -> dict[str, object]:
    return {
        "category": "special_crew",
        "name": name,
        "source": SPECIALIST_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "crew_specialist",
        "stat_effects": effects,
    }


SPECIAL_CREW_OPTIONS = [
    _specialist("Artillerist", {"cannon_damage_pct": 4}, "Broadside damage specialist."),
    _specialist("Boarding Master", {"boarding_power_pct": 9}, "Coordinates boarding parties and deck assaults."),
    _specialist("Boatswain", {"sail_hp_pct": 4, "turn_rate_pct": 2}, "Deck coordination and sail-handling specialist."),
    _specialist("Carpenter", {"repair_efficiency_pct": 6, "hull_hp_pct": 2}, "Hull repair and damage-control specialist."),
    _specialist("Chaplain", {"crew_capacity": 3, "boarding_power_pct": 2}, "Crew morale and endurance support."),
    _specialist("Cook", {"crew_capacity": 4}, "Sustains larger crews during long operations."),
    _specialist("Damage Control Officer", {"repair_efficiency_pct": 8, "fire_resistance_pct": 4}, "Coordinates repairs and fire response."),
    _specialist("Deck Officer", {"turn_rate_pct": 3, "reload_pct": 2}, "General deck and combat coordination."),
    _specialist("Engineer", {"repair_efficiency_pct": 5, "speed_pct": 2}, "Maintains ship systems and movement efficiency."),
    _specialist("Fire Marshal", {"fire_resistance_pct": 10}, "Specializes in preventing and containing fires."),
    _specialist("Gunner", {"reload_pct": 4}, "Improves gun crew tempo."),
    _specialist("Helmsman", {"turn_rate_pct": 5}, "Handling-focused steering specialist."),
    _specialist("Lookout", {"weapon_range_pct": 2}, "Target acquisition and spotting support."),
    _specialist("Marine Officer", {"boarding_power_pct": 7}, "Boarding-party commander."),
    _specialist("Master Gunner", {"reload_pct": 4, "cannon_damage_pct": 2}, "Senior gunnery specialist."),
    _specialist("Merchant", {"hold_capacity": 1200, "cargo_loss_reduction_pct": 4}, "Trade and cargo-management specialist."),
    _specialist("Mortar Officer", {"mortar_range_pct": 6, "siege_damage_pct": 4}, "Siege-fire specialist for mortar ships."),
    _specialist("Navigator", {"speed_pct": 3}, "Speed and route-keeping specialist."),
    _specialist("Powder Monkey", {"reload_pct": 3, "fire_risk_pct": 1}, "Risky close-combat reload support."),
    _specialist("Quartermaster", {"hold_capacity": 1200, "cargo_loss_reduction_pct": 5}, "Cargo and supply coordination."),
    _specialist("Sailmaker", {"sail_hp_pct": 7, "repair_efficiency_pct": 2}, "Repairs rigging and preserves sail endurance."),
    _specialist("Smuggler", {"hold_capacity": 800, "speed_pct": 2}, "Fast cargo handling and evasive logistics."),
    _specialist("Surgeon", {"crew_capacity": 6, "boarding_power_pct": 2}, "Crew sustain and attrition mitigation."),
    _specialist("Whaler", {"hold_capacity": 900, "cannon_damage_pct": 1}, "Hunting and heavy-cargo specialist."),
]
