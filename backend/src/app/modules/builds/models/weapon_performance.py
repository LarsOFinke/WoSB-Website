from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WeaponPerformanceProfile(Base):
    """Normalized sustained-fire inputs for one weapon option.

    Damage and reload belong to the weapon definition itself. Target armor and
    build modifiers remain calculation inputs and are therefore not persisted
    here.
    """

    __tablename__ = "weapon_performance_profiles"
    __table_args__ = (
        CheckConstraint("base_damage >= 0", name="ck_weapon_performance_damage"),
        CheckConstraint("reload_seconds > 0", name="ck_weapon_performance_reload"),
    )

    option_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("build_item_options.id", ondelete="CASCADE"),
        primary_key=True,
    )
    base_damage: Mapped[float] = mapped_column(Float, nullable=False)
    reload_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    option: Mapped["BuildItemOption"] = relationship(
        "BuildItemOption", back_populates="weapon_performance"
    )
