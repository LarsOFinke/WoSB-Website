from __future__ import annotations

from app.core.time import utc_now

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ShipUpgradeEffectOverride(Base):
    """Ship-specific value override for one global upgrade effect.

    Upgrade catalog options stay normalized and reusable. Only effect keys whose
    values differ for a specific ship are stored here; all other keys continue
    to inherit the global upgrade definition.
    """

    __tablename__ = "ship_upgrade_effect_overrides"
    __table_args__ = (
        UniqueConstraint(
            "ship_id",
            "option_id",
            "effect_key",
            name="uq_ship_upgrade_effect_override",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ship_id: Mapped[int] = mapped_column(
        ForeignKey("ships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_id: Mapped[int] = mapped_column(
        ForeignKey("build_item_options.id", ondelete="CASCADE"), nullable=False, index=True
    )
    effect_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    effect_value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    ship: Mapped["Ship"] = relationship("Ship", back_populates="upgrade_effect_overrides")
    option: Mapped["BuildItemOption"] = relationship("BuildItemOption", lazy="joined")

    @property
    def normalized_value(self) -> int | float:
        return int(self.effect_value) if self.effect_value.is_integer() else self.effect_value
