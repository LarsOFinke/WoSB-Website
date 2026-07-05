"""Lantern option seeds.

Lanterns are represented as their own MVP slot because the current UI mockup
contains one lantern slot and public discussions describe one lantern per
ship. Names are kept intentionally conservative until an admin-maintained
catalog can verify every event lantern.
"""

LANTERN_OPTIONS = [
    {"category": "lantern", "name": "Golden Lantern", "source": "community", "notes": "Public discussions mention golden lantern bonuses."},
    {"category": "lantern", "name": "Ice Lantern", "source": "official-news", "notes": "Listed in official New Year event rewards."},
    {"category": "lantern", "name": "Red Lantern", "source": "community", "notes": "Public discussions mention red lantern as an alternative."},
    {"category": "lantern", "name": "Storm Lantern", "source": "community", "notes": "Public social/event references mention Storm Lantern."},
]
