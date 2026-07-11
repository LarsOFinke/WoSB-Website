from __future__ import annotations

from app.core.time import utc_now

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BuildItemEffect(Base):
    __tablename__ = "build_item_effects"
    __table_args__ = (UniqueConstraint("option_id", "effect_key", name="uq_build_item_effect_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("build_item_options.id", ondelete="CASCADE"), nullable=False, index=True)
    effect_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    effect_value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    option: Mapped["BuildItemOption"] = relationship("BuildItemOption", back_populates="effects")

    @property
    def normalized_value(self) -> int | float:
        return int(self.effect_value) if self.effect_value.is_integer() else self.effect_value
