from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.ships.models.weapon_mount import WeaponClassDefinition


class ShipRateWeaponClassRule(Base):
    """Default regular-weapon class for a ship rate.

    A mount may still store an explicit class for audited exceptions. New custom
    ships use this normalized rule whenever a regular armed mount omits one.
    """

    __tablename__ = "ship_rate_weapon_class_rules"
    __table_args__ = (
        CheckConstraint("rate >= 1 and rate <= 7", name="ck_ship_rate_weapon_class_rate"),
    )

    rate: Mapped[int] = mapped_column(Integer, primary_key=True)
    weapon_class_id: Mapped[int] = mapped_column(
        ForeignKey("weapon_classes.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    weapon_class: Mapped[WeaponClassDefinition] = relationship(
        WeaponClassDefinition, lazy="joined"
    )
