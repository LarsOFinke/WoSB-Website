from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.ships.models.weapon_mount import ShipWeaponMount


class Ship(Base):
    __tablename__ = "ships"
    __table_args__ = (
        CheckConstraint("rate >= 1 and rate <= 7", name="ck_ships_rate"),
        CheckConstraint("durability >= 0", name="ck_ships_durability"),
        CheckConstraint("speed_knots >= 0", name="ck_ships_speed_knots"),
        CheckConstraint("maneuverability >= 0", name="ck_ships_maneuverability"),
        CheckConstraint("armor >= 0", name="ck_ships_armor"),
        CheckConstraint("hold_capacity >= 0", name="ck_ships_hold_capacity"),
        CheckConstraint("crew_capacity >= 0", name="ck_ships_crew_capacity"),
        CheckConstraint("sailor_minimum >= 0", name="ck_ships_sailor_minimum"),
        CheckConstraint("displacement_tons >= 0", name="ck_ships_displacement_tons"),
        CheckConstraint("sail_slots >= 0", name="ck_ships_sail_slots"),
        CheckConstraint("upgrade_slots >= 0", name="ck_ships_upgrade_slots"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    rate: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ship_type: Mapped[str] = mapped_column(String(80), nullable=False, default="Ship")
    durability: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    speed_knots: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    maneuverability: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    armor: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    hold_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    crew_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    sailor_minimum: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    displacement_tons: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str | None] = mapped_column(String(240), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sail_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    upgrade_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    has_lantern: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    seed_key: Mapped[str | None] = mapped_column(String(220), nullable=True, unique=True, index=True)
    seed_revision: Mapped[str | None] = mapped_column(String(80), nullable=True)
    seed_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_seed_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    weapon_mounts: Mapped[list["ShipWeaponMount"]] = relationship(
        "ShipWeaponMount",
        back_populates="ship",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    def _mount(self, code: str):
        return next((mount for mount in self.weapon_mounts if mount.slot_type.code == code), None)

    def weapon_capacity(self, code: str) -> int:
        mount = self._mount(code)
        return int(mount.capacity if mount is not None else 0)

    @property
    def front_weapon_capacity(self) -> int:
        return self.weapon_capacity("weapon_front")

    @property
    def broadside_weapon_capacity(self) -> int:
        return max(self.weapon_capacity("weapon_port"), self.weapon_capacity("weapon_starboard"))

    @property
    def rear_weapon_capacity(self) -> int:
        return self.weapon_capacity("weapon_rear")

    @property
    def mortar_weapon_capacity(self) -> int:
        return self.weapon_capacity("weapon_mortar")

    @property
    def special_weapon_capacity(self) -> int:
        return self.weapon_capacity("weapon_special")

    @property
    def max_mortar_caliber_inches(self) -> int | float | None:
        mount = self._mount("weapon_mortar")
        if mount is None or mount.max_caliber_inches is None:
            return None
        value = float(mount.max_caliber_inches)
        return int(value) if value.is_integer() else value

    @property
    def weapon_layout(self) -> str:
        regular = f"{self.front_weapon_capacity}-{self.broadside_weapon_capacity}-{self.rear_weapon_capacity}"
        suffixes: list[str] = []
        mortar = self._mount("weapon_mortar")
        if mortar is not None and mortar.capacity > 0:
            caliber = int(mortar.max_caliber_inches or 0)
            suffixes.append(f"mortar {caliber}in x{mortar.capacity}")
        special = self._mount("weapon_special")
        if special is not None and special.capacity > 0:
            suffixes.append(f"special x{special.capacity}")
        return f"{regular}; {'; '.join(suffixes)}" if suffixes else regular
