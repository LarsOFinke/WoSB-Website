"""Central rule for the account-wide fifth upgrade-slot reward.

The reward is not a selectable catalog item. Keeping its modifiers in one
small module prevents frontend/backend drift while the persisted boolean on a
build records whether the captain has unlocked it.
"""

from __future__ import annotations

from typing import Final

# The current game UI presents the additional slot together with a broad
# ten-percent penalty to the ship's principal base values. These normalized
# effect keys are consumed by the same stat engine as sails, lanterns,
# specialists and upgrades.
RESEARCH_UPGRADE_SLOT_EFFECTS: Final[dict[str, int | float]] = {
    "hull_hp_pct": -10,
    "speed_pct": -10,
    "turn_rate_pct": -10,
    "armor_pct": -10,
    "hold_capacity_pct": -10,
    "crew_capacity_pct": -10,
}


def research_upgrade_slot_effects(enabled: bool) -> dict[str, int | float]:
    return dict(RESEARCH_UPGRADE_SLOT_EFFECTS) if enabled else {}
