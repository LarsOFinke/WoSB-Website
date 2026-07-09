from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class BuildItemCategory(Base):
    __tablename__ = "build_item_categories"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_build_item_categories_sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    options: Mapped[list["BuildItemOption"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class BuildItemOption(Base):
    __tablename__ = "build_item_options"
    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_build_item_option_category_name"),
        CheckConstraint("sort_order >= 0", name="ck_build_item_options_sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("build_item_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    option_kind: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    allowed_slot_types: Mapped[str | None] = mapped_column(String(160), nullable=True)
    weapon_caliber_inches: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    category: Mapped[BuildItemCategory] = relationship(back_populates="options", lazy="joined")
    effects: Mapped[list["BuildItemEffect"]] = relationship(
        back_populates="option", cascade="all, delete-orphan", lazy="selectin", order_by="BuildItemEffect.effect_key"
    )

    @property
    def stat_effects(self) -> dict[str, int | float]:
        return {effect.effect_key: effect.normalized_value for effect in self.effects}

    @property
    def allowed_slots(self) -> list[str]:
        if not self.allowed_slot_types:
            return []
        return [slot.strip() for slot in self.allowed_slot_types.split(",") if slot.strip()]


class BuildItemEffect(Base):
    __tablename__ = "build_item_effects"
    __table_args__ = (UniqueConstraint("option_id", "effect_key", name="uq_build_item_effect_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("build_item_options.id", ondelete="CASCADE"), nullable=False, index=True)
    effect_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    effect_value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    option: Mapped[BuildItemOption] = relationship(back_populates="effects")

    @property
    def normalized_value(self) -> int | float:
        return int(self.effect_value) if self.effect_value.is_integer() else self.effect_value
