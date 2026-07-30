from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WeaponClassDefinition(Base):
    """Normalized weapon-size taxonomy used by both ships and weapons."""

    __tablename__ = "weapon_classes"
    __table_args__ = (CheckConstraint("rank >= 0", name="ck_weapon_classes_rank"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    ship_mounts: Mapped[list["ShipWeaponMount"]] = relationship(
        "ShipWeaponMount", back_populates="max_weapon_class"
    )
    options: Mapped[list["BuildItemOption"]] = relationship(
        "BuildItemOption", back_populates="weapon_class"
    )


class WeaponSlotType(Base):
    __tablename__ = "weapon_slot_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    ship_mounts: Mapped[list["ShipWeaponMount"]] = relationship("ShipWeaponMount", back_populates="slot_type")
    option_links: Mapped[list["BuildItemOptionSlotType"]] = relationship(
        "BuildItemOptionSlotType", back_populates="slot_type"
    )


class ShipWeaponMount(Base):
    __tablename__ = "ship_weapon_mounts"
    __table_args__ = (
        UniqueConstraint("ship_id", "slot_type_id", name="uq_ship_weapon_mount_slot"),
        CheckConstraint("capacity >= 0", name="ck_ship_weapon_mount_capacity"),
        CheckConstraint(
            "special_weapon_capacity >= 0 and special_weapon_capacity <= capacity",
            name="ck_ship_weapon_mount_special_capacity",
        ),
        CheckConstraint("max_caliber_inches is null or max_caliber_inches >= 0", name="ck_ship_weapon_mount_max_caliber"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_type_id: Mapped[int] = mapped_column(
        ForeignKey("weapon_slot_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    special_weapon_capacity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    max_weapon_class_id: Mapped[int | None] = mapped_column(
        ForeignKey("weapon_classes.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    max_caliber_inches: Mapped[float | None] = mapped_column(Float, nullable=True)

    ship: Mapped["Ship"] = relationship("Ship", back_populates="weapon_mounts")
    slot_type: Mapped[WeaponSlotType] = relationship(WeaponSlotType, back_populates="ship_mounts", lazy="joined")
    max_weapon_class: Mapped[WeaponClassDefinition | None] = relationship(
        WeaponClassDefinition, back_populates="ship_mounts", lazy="joined"
    )
