"""Ship upgrade option seeds for the Build Designer.

Upgrade effects are normalized planning modifiers. Values that are explicitly
listed in public planner/wiki/community snippets are marked as such; broader
build-planning modifiers stay conservative and documented via notes so they can
be swapped with official exports later without changing API code.
"""

UPGRADE_OPTIONS = [
    {
        "category": "upgrade",
        "name": "Ammunition Cradles",
        "source": "public-planner/community",
        "notes": "Public planner/community snippets list this as +12% reload speed.",
        "stat_effects": {"reload_pct": 12, "hold_slots": -1},
    },
    {
        "category": "upgrade",
        "name": "Cellars",
        "source": "guide/community",
        "notes": "Hold-focused planning upgrade; app effect is a conservative slot modifier until official data is available.",
        "stat_effects": {"hold_slots": 3},
    },
    {
        "category": "upgrade",
        "name": "Double Hold",
        "source": "guide/community",
        "notes": "Cargo-focused planning upgrade with cargo-loss mitigation.",
        "stat_effects": {"hold_capacity": 6500, "hold_slots": 6, "cargo_loss_reduction_pct": 40, "turn_rate_pct": -3},
    },
    {
        "category": "upgrade",
        "name": "Emergency Powder Charge",
        "source": "community",
        "notes": "Community build discussions describe this as +25% damage while below 50% HP.",
        "stat_effects": {"low_hp_damage_pct": 25, "fire_risk_pct": 4},
    },
    {
        "category": "upgrade",
        "name": "Extra Bunks",
        "source": "public-planner/guide",
        "notes": "Additional crew capacity for boarding/sustain builds.",
        "stat_effects": {"crew_capacity": 12},
    },
    {
        "category": "upgrade",
        "name": "Fortified Ports",
        "source": "community",
        "notes": "Community snippets list this range-focused upgrade as +10% cannon range.",
        "stat_effects": {"weapon_range_pct": 10},
    },
    {
        "category": "upgrade",
        "name": "Incendiary Mixture",
        "source": "guide/community",
        "notes": "Fire-oriented combat upgrade used in public build recommendations.",
        "stat_effects": {"fire_damage_pct": 10},
    },
    {
        "category": "upgrade",
        "name": "Iron Ram",
        "source": "guide/community",
        "notes": "Ramming-focused build option.",
        "stat_effects": {"ram_damage_pct": 15, "turn_rate_pct": -4},
    },
    {
        "category": "upgrade",
        "name": "Lightweight Hull",
        "source": "guide/community",
        "notes": "Speed-focused planning upgrade with a durability trade-off.",
        "stat_effects": {"speed_pct": 6, "hull_hp_pct": -6},
    },
    {
        "category": "upgrade",
        "name": "Long-Range Mortars",
        "source": "guide/community",
        "notes": "Siege/mortar planning upgrade.",
        "stat_effects": {"mortar_range_pct": 12, "reload_pct": -4},
    },
    {
        "category": "upgrade",
        "name": "Maneuverable Helm",
        "source": "community",
        "notes": "Community snippets list this as +8% mobility.",
        "stat_effects": {"turn_rate_pct": 8},
    },
    {
        "category": "upgrade",
        "name": "Reinforced Masts",
        "source": "guide/community",
        "notes": "Sail durability planning upgrade.",
        "stat_effects": {"sail_hp_pct": 12, "speed_pct": 2},
    },
    {
        "category": "upgrade",
        "name": "Repair Arsenal",
        "source": "guide/community",
        "notes": "Repair/sustain planning upgrade.",
        "stat_effects": {"repair_efficiency_pct": 10, "hold_slots": -2},
    },
    {
        "category": "upgrade",
        "name": "Structural Expansion",
        "source": "public-planner/community",
        "notes": "Public planner/search snippets list this as +2 upgrade slots with a maneuverability trade-off.",
        "stat_effects": {"extra_upgrade_slots": 2, "turn_rate_pct": -10},
    },
    {
        "category": "upgrade",
        "name": "Strong Beams",
        "source": "public-planner/guide",
        "notes": "Heavy/tank planning upgrade.",
        "stat_effects": {"hull_hp_pct": 8, "speed_pct": -3},
    },
    {
        "category": "upgrade",
        "name": "Sturdy Frames",
        "source": "guide/community",
        "notes": "Defensive planning upgrade.",
        "stat_effects": {"hull_hp_pct": 5, "crew_capacity": 4},
    },
    {
        "category": "upgrade",
        "name": "Swivel Mortars",
        "source": "guide/community",
        "notes": "Siege/boarding planning upgrade.",
        "stat_effects": {"boarding_power_pct": 8, "mortar_range_pct": 4},
    },
    {
        "category": "upgrade",
        "name": "Teak Frames",
        "source": "public-planner/guide",
        "notes": "Heavy/tank planning upgrade.",
        "stat_effects": {"hull_hp_pct": 10, "fire_resistance_pct": 6, "speed_pct": -2},
    },
]
