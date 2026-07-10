"""Build item category seeds.

Categories are intentionally small and stable. Individual option lists live in
separate files so every catalog area can grow independently.
"""

BUILD_ITEM_CATEGORIES = [
    {"key": "sail", "label": "Sails", "sort_order": 10},
    {"key": "upgrade", "label": "Upgrades", "sort_order": 20},
    {"key": "lantern", "label": "Lanterns", "sort_order": 30},
    {"key": "ammunition", "label": "Ammunition", "sort_order": 40},
    {"key": "consumable", "label": "Consumables", "sort_order": 50},
    {"key": "hold", "label": "Hold / Cargo", "sort_order": 60},
    {"key": "weapon", "label": "Weapons", "sort_order": 70},
    {"key": "special_crew", "label": "Specialists", "sort_order": 80},
]
