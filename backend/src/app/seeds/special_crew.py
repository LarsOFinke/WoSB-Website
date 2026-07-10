"""Special crew option seeds for the Build Manager prototype.

Effects are conservative planning modifiers so special crew can participate in
stat previews without pretending to be a full official export. They are stored
in the same normalized effect table as upgrades, which keeps future official
imports simple.
"""

SPECIAL_CREW_OPTIONS = [
    {
        "category": "special_crew",
        "name": "Boatswain",
        "source": "prototype/planning",
        "notes": "Deck coordination and sail handling specialist.",
        "option_kind": "crew_specialist",
        "stat_effects": {"sail_hp_pct": 4, "turn_rate_pct": 2},
    },
    {
        "category": "special_crew",
        "name": "Carpenter",
        "source": "prototype/planning",
        "notes": "Hull repair and damage-control specialist.",
        "option_kind": "crew_specialist",
        "stat_effects": {"repair_efficiency_pct": 6, "hull_hp_pct": 2},
    },
    {
        "category": "special_crew",
        "name": "Cook",
        "source": "prototype/planning",
        "notes": "Morale and endurance support.",
        "option_kind": "crew_specialist",
        "stat_effects": {"crew_capacity": 4},
    },
    {
        "category": "special_crew",
        "name": "Helmsman",
        "source": "prototype/planning",
        "notes": "Handling-focused officer.",
        "option_kind": "crew_specialist",
        "stat_effects": {"turn_rate_pct": 5},
    },
    {
        "category": "special_crew",
        "name": "Lookout",
        "source": "prototype/planning",
        "notes": "Target acquisition and spotting support.",
        "option_kind": "crew_specialist",
        "stat_effects": {"weapon_range_pct": 2},
    },
    {
        "category": "special_crew",
        "name": "Marine Officer",
        "source": "prototype/planning",
        "notes": "Boarding-party commander.",
        "option_kind": "crew_specialist",
        "stat_effects": {"boarding_power_pct": 7},
    },
    {
        "category": "special_crew",
        "name": "Master Gunner",
        "source": "prototype/planning",
        "notes": "Cannon reload and gunnery specialist.",
        "option_kind": "crew_specialist",
        "stat_effects": {"reload_pct": 4, "cannon_damage_pct": 2},
    },
    {
        "category": "special_crew",
        "name": "Mortar Officer",
        "source": "prototype/planning",
        "notes": "Siege-fire specialist for mortar ships.",
        "option_kind": "crew_specialist",
        "stat_effects": {"mortar_range_pct": 6, "siege_damage_pct": 4},
    },
    {
        "category": "special_crew",
        "name": "Navigator",
        "source": "prototype/planning",
        "notes": "Speed and route-keeping specialist.",
        "option_kind": "crew_specialist",
        "stat_effects": {"speed_pct": 3},
    },
    {
        "category": "special_crew",
        "name": "Powder Monkey",
        "source": "prototype/planning",
        "notes": "Risky reload support for close combat.",
        "option_kind": "crew_specialist",
        "stat_effects": {"reload_pct": 3, "fire_risk_pct": 1},
    },
    {
        "category": "special_crew",
        "name": "Quartermaster",
        "source": "prototype/planning",
        "notes": "Cargo and supply coordination.",
        "option_kind": "crew_specialist",
        "stat_effects": {"hold_capacity": 1200, "cargo_loss_reduction_pct": 5},
    },
    {
        "category": "special_crew",
        "name": "Surgeon",
        "source": "prototype/planning",
        "notes": "Crew sustain and attrition mitigation.",
        "option_kind": "crew_specialist",
        "stat_effects": {"crew_capacity": 6, "boarding_power_pct": 2},
    },
]
