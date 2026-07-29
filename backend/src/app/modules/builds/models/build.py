from app.core.time import utc_now
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.ships.models.ship import Ship
from app.modules.builds.services.build_stat_service import (
    apply_percentage_effects,
    build_base_stats,
    build_stat_rows,
    effective_stats_from_rows,
    round_half_up,
)
from app.modules.builds.services.upgrade_slot_service import calculate_upgrade_slot_access
from app.modules.builds.services.research_upgrade_reward import research_upgrade_slot_effects
from app.modules.builds.services.specialist_effect_service import resolve_specialist_effects
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects

if TYPE_CHECKING:
    from app.modules.accounts.models.user import User
    from app.modules.builds.models.build_classification import BuildClassification
    from app.modules.builds.models.build_slot import BuildSlot

WEAPON_SLOT_TYPE_BY_ARC = {
    "front": "weapon_front",
    "rear": "weapon_rear",
    "port": "weapon_port",
    "starboard": "weapon_starboard",
    "mortar": "weapon_mortar",
    "special": "weapon_special",
}
UPGRADE_SLOT_NUMBERS = (1, 2, 3, 4, 5, 6, 7, 8)
UPGRADE_SLOT_LIMIT = len(UPGRADE_SLOT_NUMBERS)
BASE_UPGRADE_SLOT_LIMIT = 4
DEBUFF_KEYS = {
    "speed_pct",
    "turn_rate_pct",
    "crew_capacity",
    "hull_hp_pct",
    "reload_pct",
    "weapon_range_pct",
    "boarding_power_pct",
}


class Build(Base):
    __tablename__ = "builds"
    __table_args__ = (
        CheckConstraint("sailors >= 0", name="ck_builds_sailors"),
        CheckConstraint("soldiers >= 0", name="ck_builds_soldiers"),
        CheckConstraint("musketeers >= 0", name="ck_builds_musketeers"),
        CheckConstraint("mercenaries >= 0", name="ck_builds_mercenaries"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    build_name: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    build_type: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("build_roles.slug", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        default="balanced",
        index=True,
    )
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id"), nullable=False, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    is_official_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    research_upgrade_slot_unlocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mortar_modification_installed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    sailors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    soldiers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    musketeers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mercenaries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    ship: Mapped[Ship] = relationship(lazy="joined")
    owner: Mapped["User | None"] = relationship("User", lazy="joined")
    slots: Mapped[list["BuildSlot"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="BuildSlot.slot_type, BuildSlot.slot_index",
    )
    classifications: Mapped[list["BuildClassification"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        back_populates="build",
        order_by="BuildClassification.tag",
    )

    @property
    def classification_tags(self) -> list[str]:
        return [classification.tag for classification in self.classifications]

    @property
    def build_role_label(self) -> str:
        return getattr(self, "_build_role_label", self.build_type.replace("_", " ").title())

    @property
    def upvote_count(self) -> int:
        return max(0, int(getattr(self, "_upvote_count", 0)))

    @property
    def has_upvoted(self) -> bool:
        return bool(getattr(self, "_viewer_has_upvoted", False))

    def _first_option_name(self, slot_type: str) -> str | None:
        for slot in self.slots:
            if slot.slot_type == slot_type:
                return slot.option.name
        return None

    def _option_name_at(self, slot_type: str, index: int) -> str | None:
        for slot in self.slots:
            if slot.slot_type == slot_type and slot.slot_index == index:
                return slot.option.name
        return None

    def _upgrade_slot_at(self, index: int):
        for slot in self.slots:
            if slot.slot_type == "upgrade" and slot.slot_index == index:
                return slot
        return None

    def _inventory_slots(self, slot_type: str) -> list[dict[str, Any]]:
        return [
            {"item": slot.option.name, "quantity": slot.quantity or 1}
            for slot in self.slots
            if slot.slot_type == slot_type
        ]

    def _slot_quantity_total(self, slot_type: str) -> int:
        return sum(slot.quantity or 1 for slot in self.slots if slot.slot_type == slot_type)

    @property
    def sails(self) -> str | None:
        return self._first_option_name("sail")

    @property
    def lantern(self) -> str | None:
        return self._first_option_name("lantern")

    @property
    def upgrade_1(self) -> str | None:
        return self._option_name_at("upgrade", 1)

    @property
    def upgrade_2(self) -> str | None:
        return self._option_name_at("upgrade", 2)

    @property
    def upgrade_3(self) -> str | None:
        return self._option_name_at("upgrade", 3)

    @property
    def upgrade_4(self) -> str | None:
        return self._option_name_at("upgrade", 4)

    @property
    def upgrade_5(self) -> str | None:
        return self._option_name_at("upgrade", 5)

    @property
    def upgrade_6(self) -> str | None:
        return self._option_name_at("upgrade", 6)

    @property
    def upgrade_7(self) -> str | None:
        return self._option_name_at("upgrade", 7)

    @property
    def upgrade_8(self) -> str | None:
        return self._option_name_at("upgrade", 8)

    @property
    def front_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["front"])

    @property
    def rear_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["rear"])

    @property
    def port_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["port"])

    @property
    def starboard_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["starboard"])

    @property
    def mortar_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["mortar"])

    @property
    def special_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["special"])

    @property
    def special_crew_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("special_crew")

    @property
    def ammunition_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("ammunition")

    @property
    def consumable_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("consumable")

    @property
    def hold_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("hold")

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
        research_effects = research_upgrade_slot_effects(self.research_upgrade_slot_unlocked)
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
            research_upgrade_slot_unlocked=self.research_upgrade_slot_unlocked,
        )
        expansion_upgrade_slots = self._upgrade_unlock_slot_total(
            max_index=pre_expansion_access.available_slots
        )
        upgrade_access = calculate_upgrade_slot_access(
            ship_upgrade_slots=int(self.ship.upgrade_slots or 0),
            unlock_effect_slots=expansion_upgrade_slots,
            research_upgrade_slot_unlocked=self.research_upgrade_slot_unlocked,
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
            warnings.append("Upgrade slot 5 is selected but neither the research reward nor an expansion effect unlocks it.")
        if self.upgrade_6 and not upgrade_slot_6_available:
            warnings.append("Upgrade slot 6 is selected without enough independent slot unlocks.")
        if self.upgrade_7 and not upgrade_slot_7_available:
            warnings.append("Upgrade slot 7 is selected without enough upgrade-slot capacity.")
        if self.upgrade_8 and not upgrade_slot_8_available:
            warnings.append("Upgrade slot 8 requires Structural Expansion, the research reward, and a ship-specific extra slot.")

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
