from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ShipMortarModification(Base):
    """Permanent, ship-specific conversion that exchanges stats for mortar mounts."""

    __tablename__ = "ship_mortar_modifications"
    __table_args__ = (
        CheckConstraint("mortar_capacity > 0", name="ck_ship_mortar_mod_capacity"),
        CheckConstraint(
            "max_caliber_inches > 0",
            name="ck_ship_mortar_mod_max_caliber",
        ),
        CheckConstraint(
            "broadside_capacity_delta <= 0",
            name="ck_ship_mortar_mod_broadside_delta",
        ),
        CheckConstraint(
            "durability_delta <= 0",
            name="ck_ship_mortar_mod_durability_delta",
        ),
        CheckConstraint(
            "crew_capacity_delta <= 0",
            name="ck_ship_mortar_mod_crew_delta",
        ),
        CheckConstraint(
            "speed_pct > -100 and hold_capacity_pct > -100",
            name="ck_ship_mortar_mod_percentage_range",
        ),
    )

    ship_id: Mapped[int] = mapped_column(
        ForeignKey("ships.id", ondelete="CASCADE"),
        primary_key=True,
    )
    mortar_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_caliber_inches: Mapped[float] = mapped_column(Float, nullable=False)
    broadside_capacity_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    durability_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    speed_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    maneuverability_delta: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    hold_capacity_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    crew_capacity_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(500), nullable=False)

    ship: Mapped["Ship"] = relationship("Ship", back_populates="mortar_modification")

    @property
    def stat_effects(self) -> dict[str, int | float]:
        return {
            key: value
            for key, value in {
                "durability": self.durability_delta,
                "speed_pct": self.speed_pct,
                "maneuverability": self.maneuverability_delta,
                "hold_capacity_pct": self.hold_capacity_pct,
                "crew_capacity": self.crew_capacity_delta,
            }.items()
            if value
        }
