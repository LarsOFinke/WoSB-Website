"""Project specialist catalog for the Build Designer.

World of Sea Battle B20 renamed special crew to Specialists. Public patch notes
confirm the system, but do not publish a machine-readable roster with current
names and modifiers. These 24 maintained project entries therefore keep stable
seed identities and remain editable in Admin -> Master data. Exact in-game
roster changes can be applied without breaking saved builds.
"""

SPECIALIST_CATALOG_REVISION = "B20-project-roster-24-2026-07"
SPECIALIST_CATALOG_STATUS = "project-catalog-pending-in-game-roster-audit"


def _specialist(
    seed_id: str,
    name: str,
    effects: dict[str, int | float],
    notes: str,
) -> dict[str, object]:
    return {
        "category": "special_crew",
        "seed_id": seed_id,
        "name": name,
        "source": SPECIALIST_CATALOG_REVISION,
        "notes": f"{notes} Catalog status: {SPECIALIST_CATALOG_STATUS}.",
        "option_kind": "crew_specialist",
        "stat_effects": effects,
    }


SPECIAL_CREW_OPTIONS = [
    _specialist("artillerist", "Artillerist", {"cannon_damage_pct": 4}, "Broadside damage specialist."),
    _specialist("boarding-master", "Boarding Master", {"boarding_power_pct": 9}, "Coordinates boarding parties and deck assaults."),
    _specialist("boatswain", "Boatswain", {"sail_hp_pct": 4, "turn_rate_pct": 2}, "Deck coordination and sail-handling specialist."),
    _specialist("carpenter", "Carpenter", {"repair_efficiency_pct": 6, "hull_hp_pct": 2}, "Hull repair and damage-control specialist."),
    _specialist("chaplain", "Chaplain", {"crew_capacity": 3, "boarding_power_pct": 2}, "Crew morale and endurance support."),
    _specialist("cook", "Cook", {"crew_capacity": 4}, "Sustains larger crews during long operations."),
    _specialist("damage-control-officer", "Damage Control Officer", {"repair_efficiency_pct": 8, "fire_resistance_pct": 4}, "Coordinates repairs and fire response."),
    _specialist("deck-officer", "Deck Officer", {"turn_rate_pct": 3, "reload_pct": 2}, "General deck and combat coordination."),
    _specialist("engineer", "Engineer", {"repair_efficiency_pct": 5, "speed_pct": 2}, "Maintains ship systems and movement efficiency."),
    _specialist("fire-marshal", "Fire Marshal", {"fire_resistance_pct": 10}, "Specializes in preventing and containing fires."),
    _specialist("gunner", "Gunner", {"reload_pct": 4}, "Improves gun crew tempo."),
    _specialist("helmsman", "Helmsman", {"turn_rate_pct": 5}, "Handling-focused steering specialist."),
    _specialist("lookout", "Lookout", {"weapon_range_pct": 2}, "Target acquisition and spotting support."),
    _specialist("marine-officer", "Marine Officer", {"boarding_power_pct": 7}, "Boarding-party commander."),
    _specialist("master-gunner", "Master Gunner", {"reload_pct": 4, "cannon_damage_pct": 2}, "Senior gunnery specialist."),
    _specialist("merchant", "Merchant", {"hold_capacity": 1200, "cargo_loss_reduction_pct": 4}, "Trade and cargo-management specialist."),
    _specialist("mortar-officer", "Mortar Officer", {"mortar_range_pct": 6, "siege_damage_pct": 4}, "Siege-fire specialist for mortar ships."),
    _specialist("navigator", "Navigator", {"speed_pct": 3}, "Speed and route-keeping specialist."),
    _specialist("powder-monkey", "Powder Monkey", {"reload_pct": 3, "fire_risk_pct": 1}, "Risky close-combat reload support."),
    _specialist("quartermaster", "Quartermaster", {"hold_capacity": 1200, "cargo_loss_reduction_pct": 5}, "Cargo and supply coordination."),
    _specialist("sailmaker", "Sailmaker", {"sail_hp_pct": 7, "repair_efficiency_pct": 2}, "Repairs rigging and preserves sail endurance."),
    _specialist("smuggler", "Smuggler", {"hold_capacity": 800, "speed_pct": 2}, "Fast cargo handling and evasive logistics."),
    _specialist("surgeon", "Surgeon", {"crew_capacity": 6, "boarding_power_pct": 2}, "Crew sustain and attrition mitigation."),
    _specialist("whaler", "Whaler", {"hold_capacity": 900, "cannon_damage_pct": 1}, "Hunting and heavy-cargo specialist."),
]
