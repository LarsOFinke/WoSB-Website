from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.ship import Ship


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

    def _inventory_slots(self, slot_type: str) -> list[dict[str, Any]]:
        return [
            {"item": slot.option.name, "quantity": slot.quantity or 1}
            for slot in self.slots
            if slot.slot_type == slot_type
        ]

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
    def ammunition_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("ammunition")

    @property
    def consumable_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("consumable")

    @property
    def hold_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("hold")
