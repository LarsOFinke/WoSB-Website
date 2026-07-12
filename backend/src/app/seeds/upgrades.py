"""Verified ship-upgrade catalog for the Build Designer.

The values below were transcribed from the current in-game upgrade panels. They
are the global/default values used when a ship has no explicit override. A
ship-specific sparse overlay is stored in ``ship_upgrade_effect_overrides`` and
is managed through the master-data ship editor.
"""

from __future__ import annotations

UPGRADE_CATALOG_REVISION = "WoSB in-game upgrade panels 2026-07"

# Renames are applied before the seed sync so saved build slots continue to
# reference the current catalog option instead of becoming orphaned/inactive.
LEGACY_UPGRADE_NAME_ALIASES = {
    "Additional Hammocks": "Extra Bunks",
    "Improved Gun Carriages": "Advanced Gun Carriages",
    "Reinforced Ports": "Fortified Ports",
}


def _upgrade(
    name: str,
    group: str,
    effects: dict[str, int | float],
    notes: str,
) -> dict[str, object]:
    return {
        "category": "upgrade",
        "name": name,
        "source": UPGRADE_CATALOG_REVISION,
        "notes": notes,
        "option_kind": f"ship_upgrade_{group}",
        "stat_effects": effects,
    }


UPGRADE_OPTIONS = [
    # Speed
    _upgrade(
        "Maneuverable Helm",
        "speed",
        {"turn_rate_pct": 8, "cruising_turn_speed_penalty_pct": -15},
        "Maneuverability +8%. Speed while turning at cruise speed -15%.",
    ),
    _upgrade(
        "Reinforced Masts",
        "speed",
        {"speed_knots": 0.5, "sail_efficiency": 1},
        "Speed +0.5 kn. Additional sail efficiency +1.",
    ),
    _upgrade(
        "Lightweight Hull",
        "speed",
        {"turn_rate_pct": 5, "speed_pct": 4, "armor_pct": -15},
        "Maneuverability +5%. Speed +4%. Armor -15%.",
    ),

    # Expeditionary
    _upgrade(
        "Small Hooks",
        "expeditionary",
        {"reeling_speed_pct": 250, "fishing_speed_pct": 30, "boarding_range_pct": 15},
        "Reeling speed +250%. Fishing speed +30%. Boarding range +15%.",
    ),
    _upgrade(
        "Combat Crow's Nest",
        "expeditionary",
        {"visibility_range_pct": 50, "weapon_aiming_pct": 60},
        "Visibility range +50%. Weapon aiming speed +60%.",
    ),
    _upgrade(
        "Sturdy Frames",
        "expeditionary",
        {"hull_hp_pct": 10, "hold_capacity_pct": 12, "speed_pct": -15},
        "Durability +10%. Hold +12%. Speed -15%.",
    ),
    _upgrade(
        "Double Hold",
        "expeditionary",
        {"hold_capacity": 4500, "item_loss_pct": -40, "hull_hp_pct": -5},
        "Hold +4500. Item loss -40%. Durability -5%.",
    ),
    _upgrade(
        "Extra Ballast",
        "expeditionary",
        {"ship_roll_reduction_pct": 50, "weapon_spread_pct": -40},
        "Ship roll reduced by 50%. Weapon spread -40%.",
    ),
    _upgrade(
        "Cellars",
        "expeditionary",
        {"hold_capacity": 2000, "perishable_goods_preserved_enabled": 1},
        "Hold +2000. Perishable goods do not spoil.",
    ),
    _upgrade(
        "Extra Bunks",
        "expeditionary",
        {"crew_capacity": 14, "crew_count_hidden_enabled": 1},
        "Crew +14. Crew count is hidden.",
    ),

    # Protection
    _upgrade(
        "Repair Arsenal",
        "protection",
        {"durability": 150, "repair_item_efficiency_pct": 20},
        "Durability +150. Repair item efficiency +20%.",
    ),
    _upgrade(
        "Iron Plating",
        "protection",
        {"water_fire_protection_pct": 45, "armor_pct": -10},
        "Water-fire protection +45%. Armor -10%.",
    ),
    _upgrade(
        "Copper Plating",
        "protection",
        {"water_fire_protection_pct": 25, "explosive_fire_ship_protection_pct": 30},
        "Water-fire protection +25%. Protection against gunpowder barrels and fire ships +30%.",
    ),
    _upgrade(
        "Iron Ram",
        "protection",
        {"ram_damage_pct": 20, "bow_damage_absorption_pct": 20, "quick_sinking_by_ramming_enabled": 1},
        "Ram damage +20%. Bow damage absorption +20%. Enables quick sinking by ramming.",
    ),
    _upgrade(
        "Reinforced Bolt Ropes",
        "protection",
        {"sail_protection_pct": 30, "sail_fire_protection_pct": 50},
        "Sail protection +30%. Sail fire protection +50%.",
    ),
    _upgrade(
        "Teak Frames",
        "protection",
        {"armor": 15, "crew_capacity": 10, "turn_rate_pct": -6},
        "Armor +15. Crew +10. Maneuverability -6%.",
    ),

    # Combat
    _upgrade(
        "Upper Deck",
        "combat",
        {"barrel_reload_pct": 35, "swivel_gun_reload_pct": 35},
        "Barrel reload speed +35%. Swivel-gun reload speed +35%.",
    ),
    _upgrade(
        "Ammunition Cradles",
        "combat",
        {"reload_pct": 12},
        "Reload speed +12%.",
    ),
    _upgrade(
        "Advanced Gun Carriages",
        "combat",
        {"weapon_angle": 10, "weapon_aiming_pct": 30},
        "Weapon angle +10. Weapon aiming speed +30%.",
    ),
    _upgrade(
        "Reinforced Cannons",
        "combat",
        {"bow_stern_weapon_damage_pct": 87},
        "Damage from stern and bow weapons +87%.",
    ),
    _upgrade(
        "Incendiary Mixture",
        "combat",
        {"all_ammo_ignition_enabled": 1, "projectile_speed_pct": 10},
        "Fire effects and ignition with any ammunition type. Projectile speed +10%.",
    ),
    _upgrade(
        "Fortified Ports",
        "combat",
        {"weapon_range": 10},
        "Cannon range +10.",
    ),
    _upgrade(
        "Combat Arsenal",
        "combat",
        {"item_reload_pct": 20, "ammo_switch_speed_pct": 50},
        "Item reload speed +20%. Ammunition-type switch speed +50%.",
    ),

    # Unusual
    _upgrade(
        "Strong Beams",
        "unusual",
        {"hull_hp_pct": 5, "mortar_protection_pct": 30, "speed_pct": -5},
        "Durability +5%. Mortar protection +30%. Speed -5%.",
    ),
    _upgrade(
        "Portable Chest",
        "unusual",
        {"boarding_gold_pct": 5},
        "Winning boarding attempts grants +5% gold.",
    ),
    _upgrade(
        "Emergency Powder Charge",
        "unusual",
        {"low_hp_damage_pct": 25},
        "Damage scales from +10% to +25% as durability falls, reaching the maximum at 33% durability.",
    ),
    _upgrade(
        "High Helm Port",
        "unusual",
        {"barrels_mines_third_speed_enabled": 1, "barrel_mine_radius_pct": 30},
        "Barrels and mines are available at third speed. Barrel and mine damage radius +30%.",
    ),
    _upgrade(
        "Structural Expansion",
        "unusual",
        {"extra_upgrade_slots": 2, "turn_rate_pct": -10},
        "Upgrade spaces +2. Maneuverability -10%.",
    ),

    # Mortar
    _upgrade(
        "Long-Range Mortars",
        "mortar",
        {"mortar_range": 10, "turn_rate_pct": -8},
        "Mortar range +10. Maneuverability -8%.",
    ),
    _upgrade(
        "Reinforced Centre-Line",
        "mortar",
        {"mortar_aiming_pct": 40, "mortar_dead_zone_reduction_pct": 30},
        "Mortar aiming speed +40%. Mortar dead-zone reduction +30%.",
    ),
    _upgrade(
        "Lightweight Construction",
        "mortar",
        {"mortar_reload_pct": 40, "hold_capacity_pct": 25, "mortar_damage_pct": -25},
        "Mortar reload speed +40%. Hold +25%. Mortar damage -25%.",
    ),
    _upgrade(
        "Swivel Mortars",
        "mortar",
        {"mortar_damage_pct": 12, "mortar_angle_degrees": 50, "mortar_aiming_pct": -25},
        "Mortar damage +12%. Mortar angle +50 degrees. Mortar aiming speed -25%.",
    ),
]

UPGRADE_EFFECTS_BY_NAME: dict[str, dict[str, int | float]] = {
    str(row["name"]): dict(row["stat_effects"])
    for row in UPGRADE_OPTIONS
}
