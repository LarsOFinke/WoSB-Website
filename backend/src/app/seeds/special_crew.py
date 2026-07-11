"""Verified Specialist catalog for the Build Designer.

The values in this module were transcribed from in-game Specialist tooltips
provided by the project owner on 2026-07-11. Conditional abilities keep their
own effect keys so they are displayed without being applied permanently to the
ship's base profile. Per-sailor and per-boarder values are resolved against the
crew allocation by ``specialist_effect_service``.
"""

from __future__ import annotations

SPECIALIST_CATALOG_REVISION = "B20-in-game-screenshots-2026-07-11-v2"
SPECIALIST_CATALOG_STATUS = "verified-from-project-owner-screenshots"


def _specialist(
    seed_id: str,
    name: str,
    group: str,
    effects: dict[str, int | float],
    tooltip: str,
) -> dict[str, object]:
    return {
        "category": "special_crew",
        "seed_id": seed_id,
        "name": name,
        "source": SPECIALIST_CATALOG_REVISION,
        "notes": f"Group: {group}. {tooltip} Catalog status: {SPECIALIST_CATALOG_STATUS}.",
        "option_kind": "crew_specialist",
        "stat_effects": effects,
    }


# Keep legacy stable IDs for Sail Handler and Doctor. Older builds already
# reference those seed identities; changing only the display data preserves the
# normalized option rows and avoids duplicate-name conflicts during seeding.
SPECIAL_CREW_OPTIONS = [
    # Pirates
    _specialist("corsair", "Corsair", "Pirates", {"all_experience_pct": 6}, "All experience +6%."),
    _specialist("scribe", "Scribe", "Pirates", {"branch_upgrade_experience_pct": 20}, "Experience into ship branches and upgrades +20%."),
    _specialist("mastman", "Mastman", "Pirates", {"visibility_range_pct": 10}, "Visibility range +10%."),
    _specialist("navigator", "Navigator", "Pirates", {"minimap_item_visibility_pct": 40}, "Item visibility distance on the minimap +40%."),
    _specialist("harpooner", "Harpooner", "Pirates", {"boarding_hook_reload_pct": 60}, "Boarding hook reload speed +60%."),
    _specialist("skipper", "Skipper", "Pirates", {"boarding_cargo_weight_per_boarder_pct": 0.5}, "For each boarder: maximum cargo weight captured from boarding +0.5%. Pirates and Military conflict unless Ginger is present."),
    _specialist("recruiter", "Recruiter", "Pirates", {"crew_pickup_limit": 10}, "Crew limit above the normal threshold when picking crew up at sea or during boarding +10."),
    _specialist("powder-monkey", "Powder Monkey", "Pirates", {"swivel_reload_pct": 20}, "Swivel gun reload speed +20%."),
    _specialist("daredevil", "Daredevil", "Pirates", {"sortie_death_prevention_enabled": 1}, "Crew will not die in sorties."),
    _specialist("surgeon", "Doctor", "Pirates", {"boarding_company_shelling_survivability_pct": 40}, "Boarding-company survivability during shelling +40%. Does not increase ship crew capacity."),

    # Sailors
    _specialist("first-mate", "First Mate", "Sailors", {"speed_per_sailor_pct": 0.2}, "For each assigned Sailor: speed change +0.2%."),
    _specialist("sailmaker", "Sail Handler", "Sailors", {"speed_pct": 4}, "Speed +4%."),
    _specialist("helmsman", "Helmsman", "Sailors", {"stationary_first_speed_maneuverability": 4}, "Maneuverability while stationary and at first speed +4."),
    _specialist("steersman", "Steersman", "Sailors", {"low_durability_maneuverability": 6}, "When durability is 50% or lower: maneuverability +6."),
    _specialist("rigger", "Rigger", "Sailors", {"sail_autorepair_pct": 25}, "Sail auto-repair speed +25%."),
    _specialist("carpenter", "Ship's Carpenter", "Sailors", {"second_speed_repair_enabled": 1}, "Repairs are available at second speed, but are slower."),
    _specialist("purser", "Purser", "Sailors", {"overload_speed_penalty_reduction_pct": 30}, "Reduces the speed penalty when overloaded by 30%."),
    _specialist("cook", "Cook", "Sailors", {"food_nutrition_pct": 33}, "Food nutrition +33%."),
    _specialist("clerk", "Clerk", "Sailors", {"weapon_explosion_risk_reduction_pct": 40}, "Decreases the chance of weapons blowing up by 40%."),
    _specialist("fisherman", "Fisherman", "Sailors", {"fishing_catch_per_boarder_pct": 0.5}, "For each boarder: whale-hunting and fishing catch +0.5%."),
    _specialist("boatman", "Boatman", "Sailors", {"fishing_speed_per_sailor_pct": 1}, "For each assigned Sailor: fishing speed +1%."),
    _specialist("sailing-master", "Sailing Master", "Sailors", {"steady_course_enabled": 1}, "Helps maintain a steady course."),

    # Military
    _specialist("midshipman", "Midshipman", "Military", {"boarding_musketeer_defense_enabled": 1}, "During boarding, Musketeers start defending."),
    _specialist("watchman", "Watchman", "Military", {"fire_extinguishing_pct": 40}, "Fire-extinguishing speed +40%."),
    _specialist("military-surgeon", "Surgeon", "Military", {"repair_wounded_crew_pct": 50}, "Half of the crew wounded by cannon fire is healed during repairs."),
    _specialist("sub-lieutenant", "Sub-lieutenant", "Military", {"item_reload_per_sailor_pct": 0.1}, "For each assigned Sailor: item reload +0.1%."),
    _specialist("naval-cadet", "Naval Cadet", "Military", {"npc_grapeshot_damage_pct": 33}, "Damage dealt with grapeshot against NPCs +33%."),
    _specialist("commodore", "Commodore", "Military", {"weapon_aiming_pct": 20}, "Weapon aiming speed +20%."),
    _specialist("commander", "Commander", "Military", {"ammo_switch_per_sailor_pct": 0.2}, "For each assigned Sailor: ammunition-type switch speed +0.2%."),
    _specialist("gunner", "Gunner", "Military", {"reload_pct": 4}, "Reload speed +4%."),
    _specialist("armorer", "Armorer", "Military", {"next_single_shot_reload_pct": 20}, "The next reload after firing a single cannon shot is 20% faster."),
    _specialist("master-gunner", "Master Gunner", "Military", {"low_durability_reload_per_sailor_pct": 0.1}, "For each assigned Sailor while durability is 50% or lower: weapon reload speed +0.1%. Pirates and Military conflict unless Ginger is present."),
    _specialist("artillerist", "Artillerist", "Military", {"mortar_aiming_pct": 25}, "Mortar aiming speed +25%."),

    # Adventurers
    _specialist("lifeguard", "Lifeguard", "Adventurers", {"unique_crew_empire_boarding_chance_pct": 15}, "Chance to find unique crew when boarding Empire ships +15%."),
    _specialist("explorer", "Explorer", "Adventurers", {"unique_crew_at_sea_chance_pct": 5}, "Chance to find unique crew at sea, except Adventurers, +5%."),
    _specialist("seafarer", "Seafarer", "Adventurers", {"unique_crew_save_after_mode_pct": 50}, "Chance to find and save unique crew after mode completion +50%."),
    _specialist("scout", "Scout", "Adventurers", {"boarding_captives_pct": 30}, "More captives from the total crew count when boarding +30%."),
    _specialist("lucky-one", "Lucky One", "Adventurers", {"double_items_at_sea_chance_pct": 20}, "Chance to find twice as many items at sea +20%."),
    _specialist("seeker", "Seeker", "Adventurers", {"rare_items_chance_pct": 10}, "Chance to find rare items at sea and on islands +10%."),
    _specialist("veteran", "Veteran", "Adventurers", {"consumables_no_port_timer_enabled": 1}, "Consumables picked up at sea do not receive a timer until entering a port."),
    _specialist("old-hand", "Old Hand", "Adventurers", {"shipwreck_durability_restore_pct": 5}, "Restores durability when examining a shipwreck +5%."),
    _specialist("ginger", "Ginger", "Adventurers", {"conflict_resolution_enabled": 1}, "Resolves incompatibility conflicts between Specialists."),
]

SPECIALIST_EFFECTS_BY_SEED_ID: dict[str, dict[str, int | float]] = {
    str(row["seed_id"]): dict(row["stat_effects"])
    for row in SPECIAL_CREW_OPTIONS
}
