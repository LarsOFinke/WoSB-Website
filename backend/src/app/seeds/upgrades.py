"""B20-compatible ship upgrade catalog for the Build Designer.

The game continues to rebalance individual values. The seed stores normalized
planning effects so builds remain comparable while names and known B20 behavior
stay current. Effects can be replaced later without changing saved builds.
"""

UPGRADE_CATALOG_REVISION = "B20-fleet-audit-2026-07"


def _upgrade(name: str, effects: dict[str, int | float], notes: str) -> dict[str, object]:
    return {
        "category": "upgrade",
        "name": name,
        "source": UPGRADE_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "ship_upgrade",
        "stat_effects": effects,
    }


UPGRADE_OPTIONS = [
    _upgrade("Additional Hammocks", {"crew_capacity": 10}, "Additional crew accommodation for boarding and sustain builds."),
    _upgrade("Ammunition Cradles", {"reload_pct": 12, "hold_slots": -1}, "Reload-focused gun-deck upgrade with a cargo-slot trade-off."),
    _upgrade("Armored Magazine", {"fire_resistance_pct": 8, "speed_pct": -1}, "Protects powder storage at a small mobility cost."),
    _upgrade("Boarding Nets", {"boarding_power_pct": 8, "speed_pct": -1}, "Boarding-defense and close-action preparation."),
    _upgrade("Braced Gun Carriages", {"cannon_damage_pct": 5, "turn_rate_pct": -2}, "Stabilized gun mounts for heavier broadsides."),
    _upgrade("Cellars", {"hold_slots": 3}, "Adds organized cargo and ammunition storage."),
    _upgrade("Copper Plating", {"speed_pct": 4, "turn_rate_pct": 2}, "Mobility-focused hull treatment."),
    _upgrade("Double Hold", {"hold_capacity": 6500, "hold_slots": 6, "cargo_loss_reduction_pct": 40, "turn_rate_pct": -3}, "Large logistics conversion with a maneuverability trade-off."),
    _upgrade("Emergency Powder Charge", {"low_hp_damage_pct": 25, "fire_risk_pct": 4}, "B20 behavior: bonus scales as durability falls and reaches +25% at 33% durability."),
    _upgrade("Expanded Galley", {"crew_capacity": 8, "hold_slots": -1}, "Long-duration crew support at the cost of one hold slot."),
    _upgrade("Extra Bunks", {"crew_capacity": 12}, "Additional crew capacity for boarding and sustain builds."),
    _upgrade("Fireproof Compartments", {"fire_resistance_pct": 12, "hold_capacity": -500}, "Fire protection with reduced cargo volume."),
    _upgrade("Gun Deck Reinforcement", {"cannon_damage_pct": 4, "hull_hp_pct": 4, "speed_pct": -2}, "Structural support for heavy gunnery builds."),
    _upgrade("Improved Bilge Pumps", {"repair_efficiency_pct": 8, "crew_capacity": -2}, "Damage-control upgrade requiring dedicated crew."),
    _upgrade("Improved Gun Carriages", {"reload_pct": 6, "weapon_range_pct": 3}, "General-purpose gunnery handling upgrade."),
    _upgrade("Incendiary Mixture", {"fire_damage_pct": 10, "fire_risk_pct": 2}, "Fire-oriented combat upgrade with handling risk."),
    _upgrade("Iron Ram", {"ram_damage_pct": 15, "turn_rate_pct": -4}, "Ramming-focused bow reinforcement."),
    _upgrade("Light Rigging", {"speed_pct": 5, "sail_hp_pct": -7}, "Higher speed with reduced sail durability."),
    _upgrade("Lightweight Hull", {"speed_pct": 6, "hull_hp_pct": -6}, "Speed-focused hull conversion with reduced durability."),
    _upgrade("Long-Range Mortars", {"mortar_range_pct": 12, "reload_pct": -4}, "Siege range at the expense of reload tempo."),
    _upgrade("Maneuverable Helm", {"turn_rate_pct": 8}, "Mobility-focused steering upgrade."),
    _upgrade("Powder Magazine", {"reload_pct": 7, "fire_risk_pct": 3}, "Faster ammunition handling with increased fire risk."),
    _upgrade("Reinforced Bulkheads", {"hull_hp_pct": 7, "hold_capacity": -700}, "Defensive internal reinforcement."),
    _upgrade("Reinforced Masts", {"sail_hp_pct": 12, "speed_pct": 2}, "Improves sail durability while preserving speed."),
    _upgrade("Reinforced Ports", {"weapon_range_pct": 10}, "Current B20 name; the range bonus also interacts correctly with White Double Powder."),
    _upgrade("Reinforced Rudder", {"turn_rate_pct": 6, "hull_hp_pct": 2}, "Steering protection and maneuverability."),
    _upgrade("Repair Arsenal", {"repair_efficiency_pct": 10, "hold_slots": -2}, "Carries dedicated repair stores in exchange for cargo slots."),
    _upgrade("Sailmaker's Workshop", {"sail_hp_pct": 8, "repair_efficiency_pct": 4, "hold_slots": -1}, "Sail sustain for long operations."),
    _upgrade("Spare Yards", {"sail_hp_pct": 6, "hold_capacity": -600}, "Replacement spars improve rigging endurance."),
    _upgrade("Structural Expansion", {"extra_upgrade_slots": 2, "turn_rate_pct": -10}, "Adds two upgrade slots with a major maneuverability penalty."),
    _upgrade("Strong Beams", {"hull_hp_pct": 8, "speed_pct": -3}, "Heavy defensive reinforcement."),
    _upgrade("Sturdy Frames", {"hull_hp_pct": 5, "crew_capacity": 4}, "Balanced hull and crew-support reinforcement."),
    _upgrade("Swivel Mortars", {"boarding_power_pct": 8, "mortar_range_pct": 4}, "Close-range siege and boarding support."),
    _upgrade("Teak Frames", {"hull_hp_pct": 10, "fire_resistance_pct": 6, "speed_pct": -2}, "Premium defensive framing with a mobility cost."),
]
