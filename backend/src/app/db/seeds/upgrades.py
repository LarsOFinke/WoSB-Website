"""Ship upgrade option seeds.

The catalog keeps compact stat modifiers next to the visible option names.
The modifiers are app-level planning values used by the Build Manager preview;
they can be replaced later by official data without changing the service layer.
"""

UPGRADE_OPTIONS = [{'category': 'upgrade', 'name': 'Ammunition Cradles', 'source': 'public-planner/guide', 'notes': 'Listed by public planner/search snippets and build discussions as a reload-speed upgrade.', 'stat_effects': {'reload_pct': 8, 'hold_slots': -1}},
    {'category': 'upgrade', 'name': 'Cellars', 'source': 'guide', 'notes': 'Referenced for transport/hold-focused builds.', 'stat_effects': {'hold_slots': 3, 'speed_pct': -2}},
    {'category': 'upgrade', 'name': 'Double Hold', 'source': 'guide', 'notes': 'Referenced for cargo capacity and loss reduction.', 'stat_effects': {'hold_slots': 6, 'speed_pct': -4, 'turn_rate_pct': -3}},
    {'category': 'upgrade', 'name': 'Emergency Powder Charge', 'source': 'guide/community', 'notes': 'Referenced for siege/mortar builds.', 'stat_effects': {'siege_damage_pct': 10, 'fire_risk_pct': 4}},
    {'category': 'upgrade', 'name': 'Extra Bunks', 'source': 'public-planner/guide', 'notes': 'Public planner/search snippets list Extra Bunks with additional crew.', 'stat_effects': {'crew_capacity': 12, 'speed_pct': -2}},
    {'category': 'upgrade', 'name': 'Fortified Gun Ports', 'source': 'guide', 'notes': 'Referenced in speed and combat recommendations.', 'stat_effects': {'weapon_range_pct': 5, 'hull_hp_pct': 4, 'speed_pct': -2}},
    {'category': 'upgrade', 'name': 'Fortified Ports', 'source': 'guide/community', 'notes': 'Common short name in build recommendations for range-focused builds.', 'stat_effects': {'weapon_range_pct': 7, 'turn_rate_pct': -2}},
    {'category': 'upgrade', 'name': 'Incendiary Mixture', 'source': 'guide/community', 'notes': 'Referenced for fire-oriented combat builds.', 'stat_effects': {'fire_damage_pct': 12, 'reload_pct': -3}},
    {'category': 'upgrade', 'name': 'Iron Ram', 'source': 'guide', 'notes': 'Referenced for ramming builds.', 'stat_effects': {'ram_damage_pct': 15, 'turn_rate_pct': -4}},
    {'category': 'upgrade', 'name': 'Lightweight Hull', 'source': 'guide', 'notes': 'Referenced for speed/trade builds.', 'stat_effects': {'speed_pct': 6, 'hull_hp_pct': -6}},
    {'category': 'upgrade', 'name': 'Long-Range Mortars', 'source': 'guide', 'notes': 'Referenced as a core siege/mortar build upgrade.', 'stat_effects': {'mortar_range_pct': 12, 'reload_pct': -4}},
    {'category': 'upgrade', 'name': 'Reinforced Masts', 'source': 'guide', 'notes': 'Referenced in speed recommendations.', 'stat_effects': {'sail_hp_pct': 12, 'speed_pct': 2}},
    {'category': 'upgrade', 'name': 'Repair Arsenal', 'source': 'guide', 'notes': 'Referenced in tank/sustain builds.', 'stat_effects': {'repair_efficiency_pct': 10, 'hold_slots': -2}},
    {'category': 'upgrade', 'name': 'Structural Expansion', 'source': 'public-planner/guide', 'notes': 'Unlocks the fifth upgrade slot and applies expansion debuffs.', 'stat_effects': {'extra_upgrade_slots': 1, 'crew_capacity': -8, 'speed_pct': -5, 'turn_rate_pct': -5}},
    {'category': 'upgrade', 'name': 'Strong Beams', 'source': 'public-planner/guide', 'notes': 'Referenced in heavy/tank recommendations and planner snippets.', 'stat_effects': {'hull_hp_pct': 8, 'speed_pct': -3}},
    {'category': 'upgrade', 'name': 'Sturdy Frames', 'source': 'guide', 'notes': 'Referenced in tank and hold recommendations.', 'stat_effects': {'hull_hp_pct': 5, 'crew_capacity': 4}},
    {'category': 'upgrade', 'name': 'Swivel Mortars', 'source': 'guide', 'notes': 'Referenced as a siege/mortar upgrade.', 'stat_effects': {'boarding_power_pct': 8, 'mortar_range_pct': 4}},
    {'category': 'upgrade', 'name': 'Teak Frames', 'source': 'public-planner/guide', 'notes': 'Referenced in heavy/tank recommendations and planner snippets.', 'stat_effects': {'hull_hp_pct': 10, 'fire_resistance_pct': 6, 'speed_pct': -2}}]
