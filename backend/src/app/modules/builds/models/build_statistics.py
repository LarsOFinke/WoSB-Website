from typing import Any

from app.modules.builds.models.build_constants import (
    DEBUFF_KEYS,
    UPGRADE_SLOT_NUMBERS,
    WEAPON_SLOT_TYPE_BY_ARC,
)
from app.modules.builds.services.build_stat_service import (
    apply_percentage_effects,
    build_base_stats,
    build_stat_rows,
    effective_stats_from_rows,
    round_half_up,
)
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects
from app.modules.builds.services.specialist_effect_service import resolve_specialist_effects
from app.modules.builds.services.upgrade_slot_service import calculate_upgrade_slot_access


class BuildStatisticsMixin:
    def _slot_effect_sets(self, slot_types: set[str]) -> list[dict[str, int | float]]:
        return [
            dict(slot.option.stat_effects)
            for slot in self.slots
            if slot.slot_type in slot_types
        ]

    def _slot_effect_totals(self, slot_types: set[str]) -> dict[str, int | float]:
        return self._combine_effects(*self._slot_effect_sets(slot_types))

    def _upgrade_effect_sets(self, max_index: int | None = None) -> list[dict[str, int | float]]:
        rows: list[dict[str, int | float]] = []
        for index in UPGRADE_SLOT_NUMBERS:
            if max_index is not None and index > max_index:
                continue
            slot = self._upgrade_slot_at(index)
            if slot is None:
                continue
            rows.append(effective_upgrade_effects(slot.option, self.ship))
        return rows

    def _upgrade_effect_totals(self, max_index: int | None = None) -> dict[str, int | float]:
        return self._combine_effects(*self._upgrade_effect_sets(max_index))

    def _upgrade_unlock_slot_total(self, max_index: int) -> int:
        """Return gross rack positions granted by installed expansion upgrades.

        Structural Expansion grants two positions exactly as shown in-game.
        The upgrade still occupies one selected position, so its own occupancy
        is already represented by the build and must not be subtracted here.
        Ship-specific overrides remain authoritative.
        """

        total = 0
        for index in UPGRADE_SLOT_NUMBERS:
            if index > max_index:
                continue
            slot = self._upgrade_slot_at(index)
            if slot is None:
                continue
            total += max(
                0,
                int(effective_upgrade_effects(slot.option, self.ship).get("extra_upgrade_slots", 0) or 0),
            )
        return total

    def _special_crew_effect_sets(self) -> list[dict[str, int | float]]:
        return [
            resolve_specialist_effects(
                [(slot.option.stat_effects, 1)],
                sailors=self.sailors,
                soldiers=self.soldiers,
                musketeers=self.musketeers,
                mercenaries=self.mercenaries,
            )
            for slot in self.slots
            if slot.slot_type == "special_crew"
        ]

    def _special_crew_effect_totals(self) -> dict[str, int | float]:
        return self._combine_effects(*self._special_crew_effect_sets())

    @staticmethod
    def _combine_effects(*effect_sets: dict[str, int | float]) -> dict[str, int | float]:
        totals: dict[str, int | float] = {}
        for effect_set in effect_sets:
            for key, value in effect_set.items():
                totals[key] = totals.get(key, 0) + value
        return totals

    @property
    def ship_stats(self) -> dict[str, Any]:
        sail_effect_sets = self._slot_effect_sets({"sail"})
        lantern_effect_sets = self._slot_effect_sets({"lantern"})
        upgrade_effect_sets = self._upgrade_effect_sets()
        sail_effects = self._combine_effects(*sail_effect_sets)
        lantern_effects = self._combine_effects(*lantern_effect_sets)
        upgrade_effects = self._combine_effects(*upgrade_effect_sets)
        special_crew_effect_sets = self._special_crew_effect_sets()
        special_crew_effects = self._combine_effects(*special_crew_effect_sets)
        research_effects = self.research_upgrade_slot_effects
        mortar_modification_effects = self.ship.mortar_modification_effects(
            self.mortar_modification_installed
        )
        effect_sets = [
            *([mortar_modification_effects] if mortar_modification_effects else []),
            *sail_effect_sets,
            *lantern_effect_sets,
            *upgrade_effect_sets,
            *special_crew_effect_sets,
            *([research_effects] if research_effects else []),
        ]
        effects = self._combine_effects(*effect_sets)
        crew_total = self.sailors + self.soldiers + self.musketeers + self.mercenaries
        base_crew_capacity = self.ship.crew_capacity
        effective_crew_capacity = max(
            0,
            round_half_up(
                apply_percentage_effects(
                    base_crew_capacity,
                    "crew_capacity_pct",
                    effect_sets,
                    fallback_total=float(effects.get("crew_capacity_pct", 0) or 0),
                )
                + float(effects.get("crew_capacity", 0) or 0)
            ),
        )
        base_sailor_minimum = self.ship.sailor_minimum
        effective_sailor_minimum = max(0, base_sailor_minimum + int(effects.get("sailor_minimum", 0)))
        sailing_efficiency_pct = (
            100
            if effective_sailor_minimum <= 0
            else min(100, max(0, round_half_up((self.sailors / effective_sailor_minimum) * 100)))
        )
        weapon_slots = {
            arc: self._slot_quantity_total(slot_type)
            for arc, slot_type in WEAPON_SLOT_TYPE_BY_ARC.items()
        }
        weapon_capacity = {
            "front": self.ship.effective_weapon_capacity(
                "weapon_front",
                mortar_modification_installed=self.mortar_modification_installed,
            ),
            "rear": self.ship.effective_weapon_capacity(
                "weapon_rear",
                mortar_modification_installed=self.mortar_modification_installed,
            ),
            "port": self.ship.effective_weapon_capacity(
                "weapon_port",
                mortar_modification_installed=self.mortar_modification_installed,
            ),
            "starboard": self.ship.effective_weapon_capacity(
                "weapon_starboard",
                mortar_modification_installed=self.mortar_modification_installed,
            ),
            "mortar": self.ship.effective_weapon_capacity(
                "weapon_mortar",
                mortar_modification_installed=self.mortar_modification_installed,
            ),
            "special": self.ship.effective_weapon_capacity(
                "weapon_special",
                mortar_modification_installed=self.mortar_modification_installed,
            ),
        }
        ammunition_count = len(self.ammunition_slots)
        consumable_count = len(self.consumable_slots)
        hold_count = len(self.hold_slots)
        upgrade_names = [getattr(self, f"upgrade_{index}") for index in UPGRADE_SLOT_NUMBERS]
        upgrade_slots_used = sum(1 for name in upgrade_names if name)
        extra_upgrade_slots = max(0, int(upgrade_effects.get("extra_upgrade_slots", 0) or 0))
        pre_expansion_access = calculate_upgrade_slot_access(
            ship_upgrade_slots=int(self.ship.upgrade_slots or 0),
            unlock_effect_slots=0,
            research_upgrade_slots=self.research_upgrade_slots,
        )
        expansion_upgrade_slots = self._upgrade_unlock_slot_total(
            max_index=pre_expansion_access.available_slots
        )
        upgrade_access = calculate_upgrade_slot_access(
            ship_upgrade_slots=int(self.ship.upgrade_slots or 0),
            unlock_effect_slots=expansion_upgrade_slots,
            research_upgrade_slots=self.research_upgrade_slots,
        )
        base_upgrade_slots_available = upgrade_access.base_slots
        upgrade_slot_5_unlocked = upgrade_access.slot_5_unlocked
        ship_extra_upgrade_slots = upgrade_access.ship_extra_slots
        upgrade_slot_6_available = upgrade_access.slot_6_available
        upgrade_slot_7_available = upgrade_access.slot_7_available
        upgrade_slot_8_available = upgrade_access.slot_8_available
        upgrade_slots_available = upgrade_access.available_slots
        # Backward-compatible alias retained for existing frontend/API consumers.
        upgrade_slot_6_unlocked = upgrade_slot_6_available
        stat_rows = build_stat_rows(self.ship, effects, effect_sets=effect_sets)
        base_stats = build_base_stats(self.ship)
        effective_stats = effective_stats_from_rows(stat_rows)
        debuffs = {key: value for key, value in effects.items() if value < 0 or key.startswith("debuff_") or key in DEBUFF_KEYS and value < 0}
        buffs = {key: value for key, value in effects.items() if key not in debuffs and key != "extra_upgrade_slots"}
        warnings: list[str] = []
        if crew_total > effective_crew_capacity:
            warnings.append("Crew exceeds effective capacity after upgrade modifiers.")
        if self.sailors < effective_sailor_minimum:
            warnings.append("Sailor count is below the required minimum.")
        if self.upgrade_5 and not upgrade_slot_5_unlocked:
            warnings.append("Upgrade slot 5 is selected but neither the upgrade add-on slot nor an expansion effect unlocks it.")
        if self.upgrade_6 and not upgrade_slot_6_available:
            warnings.append("Upgrade slot 6 is selected without enough independent slot unlocks.")
        if self.upgrade_7 and not upgrade_slot_7_available:
            warnings.append("Upgrade slot 7 is selected without enough upgrade-slot capacity.")
        if self.upgrade_8 and not upgrade_slot_8_available:
            warnings.append("Upgrade slot 8 requires Structural Expansion, the upgrade add-on slot, and a ship-specific extra slot.")

        return {
            "crew_total": crew_total,
            "crew_capacity": effective_crew_capacity,
            "base_crew_capacity": base_crew_capacity,
            "effective_crew_capacity": effective_crew_capacity,
            "crew_remaining": max(effective_crew_capacity - crew_total, 0),
            "sailor_minimum": effective_sailor_minimum,
            "base_sailor_minimum": base_sailor_minimum,
            "effective_sailor_minimum": effective_sailor_minimum,
            # Backward-compatible aliases for existing clients.
            "sailor_target": effective_sailor_minimum,
            "base_sailor_target": base_sailor_minimum,
            "effective_sailor_target": effective_sailor_minimum,
            "sailing_efficiency_pct": sailing_efficiency_pct,
            "sailors_required_met": self.sailors >= effective_sailor_minimum,
            "upgrade_slots_used": upgrade_slots_used,
            "upgrade_slots_available": upgrade_slots_available,
            "base_upgrade_slots_available": base_upgrade_slots_available,
            "extra_upgrade_slots": extra_upgrade_slots,
            "expansion_upgrade_slots": expansion_upgrade_slots,
            "research_upgrade_slots": upgrade_access.research_slots,
            "ship_extra_upgrade_slots": ship_extra_upgrade_slots,
            "upgrade_slot_5_unlocked": upgrade_slot_5_unlocked,
            "upgrade_slot_6_available": upgrade_slot_6_available,
            "upgrade_slot_6_unlocked": upgrade_slot_6_unlocked,
            "upgrade_slot_7_available": upgrade_slot_7_available,
            "upgrade_slot_8_available": upgrade_slot_8_available,
            "item_effects": effects,
            "sail_effects": sail_effects,
            "lantern_effects": lantern_effects,
            "upgrade_effects": upgrade_effects,
            "special_crew_effects": special_crew_effects,
            "research_upgrade_slot_effects": research_effects,
            "mortar_modification_installed": self.mortar_modification_installed,
            "mortar_modification_effects": mortar_modification_effects,
            "upgrade_buffs": buffs,
            "upgrade_debuffs": debuffs,
            "base_stats": base_stats,
            "effective_stats": effective_stats,
            "stat_rows": stat_rows,
            "stat_warnings": warnings,
            "weapon_slots": weapon_slots,
            "weapon_capacity": weapon_capacity,
            "weapon_total": sum(weapon_slots.values()),
            "weapon_capacity_total": sum(weapon_capacity.values()),
            "special_crew_total": len(self.special_crew_slots),
            "inventory_slots_used": ammunition_count + consumable_count + hold_count,
            "ammunition_slots_used": ammunition_count,
            "consumable_slots_used": consumable_count,
            "hold_slots_used": hold_count,
        }
