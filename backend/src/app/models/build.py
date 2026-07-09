from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.ship import Ship

WEAPON_SLOT_TYPE_BY_ARC = {
    "front": "weapon_front",
    "rear": "weapon_rear",
    "port": "weapon_port",
    "starboard": "weapon_starboard",
}
UPGRADE_SLOT_NUMBERS = (1, 2, 3, 4, 5, 6)
BASE_UPGRADE_SLOT_LIMIT = 4
UNLOCKABLE_UPGRADE_SLOT = 5
SHIP_EXTRA_UPGRADE_SLOT = 6
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    build_name: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    build_type: Mapped[str] = mapped_column(String(32), nullable=False, default="balanced", index=True)
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id"), nullable=False, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    sailors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    soldiers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    musketeers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mercenaries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    ship: Mapped[Ship] = relationship(lazy="joined")
    owner: Mapped["User | None"] = relationship("User", lazy="joined")
    slots: Mapped[list["BuildSlot"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="BuildSlot.slot_type, BuildSlot.slot_index",
    )

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

    def _upgrade_effect_totals(self, max_index: int | None = None) -> dict[str, int | float]:
        totals: dict[str, int | float] = {}
        for index in UPGRADE_SLOT_NUMBERS:
            if max_index is not None and index > max_index:
                continue
            slot = self._upgrade_slot_at(index)
            if slot is None:
                continue
            for key, value in slot.option.stat_effects.items():
                totals[key] = totals.get(key, 0) + value
        return totals

    @property
    def ship_stats(self) -> dict[str, Any]:
        effects = self._upgrade_effect_totals()
        unlock_effects = self._upgrade_effect_totals(max_index=BASE_UPGRADE_SLOT_LIMIT)
        crew_total = self.sailors + self.soldiers + self.musketeers + self.mercenaries
        base_crew_capacity = self.ship.crew_capacity
        effective_crew_capacity = max(0, base_crew_capacity + int(effects.get("crew_capacity", 0)))
        base_sailor_minimum = self.ship.sailor_minimum
        effective_sailor_minimum = max(0, base_sailor_minimum + int(effects.get("sailor_minimum", 0)))
        weapon_slots = {
            arc: self._slot_quantity_total(slot_type)
            for arc, slot_type in WEAPON_SLOT_TYPE_BY_ARC.items()
        }
        ammunition_count = len(self.ammunition_slots)
        consumable_count = len(self.consumable_slots)
        hold_count = len(self.hold_slots)
        upgrade_names = [getattr(self, f"upgrade_{index}") for index in UPGRADE_SLOT_NUMBERS]
        upgrade_slots_used = sum(1 for name in upgrade_names if name)
        base_upgrade_slots_available = min(max(int(self.ship.upgrade_slots or 0), 0), BASE_UPGRADE_SLOT_LIMIT)
        extra_upgrade_slots = max(0, int(unlock_effects.get("extra_upgrade_slots", 0)))
        upgrade_slot_5_unlocked = int(self.ship.upgrade_slots or 0) >= UNLOCKABLE_UPGRADE_SLOT and extra_upgrade_slots > 0
        ship_extra_upgrade_slots = 1 if int(self.ship.upgrade_slots or 0) >= SHIP_EXTRA_UPGRADE_SLOT else 0
        upgrade_slot_6_available = ship_extra_upgrade_slots > 0
        upgrade_slots_available = min(
            6,
            base_upgrade_slots_available
            + (1 if upgrade_slot_5_unlocked else 0)
            + ship_extra_upgrade_slots,
        )
        # Backward-compatible name for existing frontend/API consumers.
        upgrade_slot_6_unlocked = upgrade_slot_6_available
        debuffs = {key: value for key, value in effects.items() if value < 0 or key.startswith("debuff_") or key in DEBUFF_KEYS and value < 0}
        buffs = {key: value for key, value in effects.items() if key not in debuffs and key != "extra_upgrade_slots"}
        warnings: list[str] = []
        if crew_total > effective_crew_capacity:
            warnings.append("Crew exceeds effective capacity after upgrade modifiers.")
        if self.sailors < effective_sailor_minimum:
            warnings.append("Sailor count is below the effective minimum after upgrade modifiers.")
        if self.upgrade_5 and not upgrade_slot_5_unlocked:
            warnings.append("Upgrade slot 5 is selected but not unlocked by the current upgrades.")
        if self.upgrade_6 and not upgrade_slot_6_available:
            warnings.append("Upgrade slot 6 is selected but this ship has no extra upgrade slot.")

        return {
            "crew_total": crew_total,
            "crew_capacity": effective_crew_capacity,
            "base_crew_capacity": base_crew_capacity,
            "effective_crew_capacity": effective_crew_capacity,
            "crew_remaining": max(effective_crew_capacity - crew_total, 0),
            "sailor_minimum": effective_sailor_minimum,
            "base_sailor_minimum": base_sailor_minimum,
            "effective_sailor_minimum": effective_sailor_minimum,
            "sailors_required_met": self.sailors >= effective_sailor_minimum,
            "upgrade_slots_used": upgrade_slots_used,
            "upgrade_slots_available": upgrade_slots_available,
            "base_upgrade_slots_available": base_upgrade_slots_available,
            "extra_upgrade_slots": extra_upgrade_slots,
            "ship_extra_upgrade_slots": ship_extra_upgrade_slots,
            "upgrade_slot_5_unlocked": upgrade_slot_5_unlocked,
            "upgrade_slot_6_available": upgrade_slot_6_available,
            "upgrade_slot_6_unlocked": upgrade_slot_6_unlocked,
            "upgrade_effects": effects,
            "upgrade_buffs": buffs,
            "upgrade_debuffs": debuffs,
            "stat_warnings": warnings,
            "weapon_slots": weapon_slots,
            "weapon_total": sum(weapon_slots.values()),
            "special_crew_total": self._slot_quantity_total("special_crew"),
            "inventory_slots_used": ammunition_count + consumable_count + hold_count,
            "ammunition_slots_used": ammunition_count,
            "consumable_slots_used": consumable_count,
            "hold_slots_used": hold_count,
        }
