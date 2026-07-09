DEMO_BUILD_DATA = [
    {
        "build_name": "Victory Defensive Line",
        "ship_name": "Victory",
        "build_type": "defensive",
        "sails": "Tarpaulin Sails",
        "upgrade_1": "Sturdy Frames",
        "upgrade_2": "Strong Beams",
        "upgrade_3": "Repair Arsenal",
        "upgrade_4": "Structural Expansion",
        "upgrade_5": "Fortified Ports",
        "upgrade_6": "Teak Frames",
        "lantern": "Golden Lantern",
        "sailors": 82,
        "soldiers": 42,
        "musketeers": 56,
        "mercenaries": 18,
        "front_weapon_slots": [
            {"item": "Basilisk", "quantity": 2},
        ],
        "rear_weapon_slots": [
            {"item": "12-pdr Carronade", "quantity": 2},
        ],
        "port_weapon_slots": [
            {"item": "32-pdr Cannon", "quantity": 18},
        ],
        "starboard_weapon_slots": [
            {"item": "32-pdr Cannon", "quantity": 18},
        ],
        "mortar_weapon_slots": [],
        "special_crew_slots": [
            {"item": "Master Gunner", "quantity": 1},
            {"item": "Carpenter", "quantity": 1},
        ],
        "ammunition_slots": [
            {"item": "Round Shots", "quantity": 240},
            {"item": "Bar Shots", "quantity": 90},
        ],
        "consumable_slots": [
            {"item": "Iron Repair Kit", "quantity": 12},
            {"item": "Smoke Screen", "quantity": 4},
        ],
        "hold_slots": [
            {"item": "Wood", "quantity": 120},
            {"item": "Iron", "quantity": 80},
            {"item": "Fresh Meat", "quantity": 40},
        ],
        "details": "Demo build for line/sustain play. The data model is normalized; slots reference the option catalog.",
    },
    {
        "build_name": "Surprise Gunnery Scout",
        "ship_name": "Surprise",
        "build_type": "gunnery",
        "sails": "Elite Sails",
        "upgrade_1": "Ammunition Cradles",
        "upgrade_2": "Fortified Ports",
        "upgrade_3": "Lightweight Hull",
        "lantern": "Red Lantern",
        "sailors": 45,
        "soldiers": 14,
        "musketeers": 26,
        "mercenaries": 6,
        "front_weapon_slots": [],
        "rear_weapon_slots": [
            {"item": "Twin 14-pdr", "quantity": 2},
        ],
        "port_weapon_slots": [
            {"item": "16-pdr Culverin", "quantity": 8},
        ],
        "starboard_weapon_slots": [
            {"item": "16-pdr Culverin", "quantity": 8},
        ],
        "mortar_weapon_slots": [],
        "special_crew_slots": [
            {"item": "Navigator", "quantity": 1},
            {"item": "Lookout", "quantity": 1},
        ],
        "ammunition_slots": [
            {"item": "Bar Shots", "quantity": 120},
            {"item": "Grapeshot", "quantity": 60},
        ],
        "consumable_slots": [
            {"item": "Smoke Bomb", "quantity": 4},
            {"item": "Small Additional Sails", "quantity": 6},
        ],
        "hold_slots": [
            {"item": "Wood", "quantity": 45},
            {"item": "Fabric", "quantity": 30},
        ],
        "details": "Fast sample build for scouting and pressure on sails/positioning.",
    },

    {
        "build_name": "Adventure Mortar Support",
        "ship_name": "Adventure",
        "build_type": "gunnery",
        "sails": "Imported Sails",
        "upgrade_1": "Long-Range Mortars",
        "upgrade_2": "Swivel Mortars",
        "upgrade_3": "Maneuverable Helm",
        "lantern": "Storm Lantern",
        "sailors": 56,
        "soldiers": 20,
        "musketeers": 36,
        "mercenaries": 8,
        "front_weapon_slots": [],
        "rear_weapon_slots": [],
        "port_weapon_slots": [],
        "starboard_weapon_slots": [],
        "mortar_weapon_slots": [
            {"item": "10-inch Mortar", "quantity": 2},
        ],
        "special_crew_slots": [
            {"item": "Mortar Officer", "quantity": 1},
            {"item": "Navigator", "quantity": 1},
        ],
        "ammunition_slots": [
            {"item": "Round Shots", "quantity": 180},
            {"item": "Heated Shots", "quantity": 80},
        ],
        "consumable_slots": [
            {"item": "Iron Repair Kit", "quantity": 8},
        ],
        "hold_slots": [
            {"item": "Wood", "quantity": 90},
            {"item": "Fabric", "quantity": 45},
        ],
        "details": "Siege sample build that exercises the dedicated mortar slot and caliber validation.",
    },
]
