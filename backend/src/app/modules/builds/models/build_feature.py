from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BuildFeatureDefinition(Base):
    """Normalized, repository-owned build feature definition.

    Features are not selectable inventory items. They model persistent build
    toggles whose slot grants and stat effects must remain data-driven.
    """

    __tablename__ = "build_features"
    __table_args__ = (
        CheckConstraint(
            "upgrade_slots_granted >= 0 and upgrade_slots_granted <= 8",
            name="ck_build_features_upgrade_slots_granted",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    upgrade_slots_granted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    effects: Mapped[list["BuildFeatureEffect"]] = relationship(
        "BuildFeatureEffect",
        back_populates="feature",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="BuildFeatureEffect.effect_key",
    )

    @property
    def stat_effects(self) -> dict[str, int | float]:
        return {effect.effect_key: effect.normalized_value for effect in self.effects}


class BuildFeatureEffect(Base):
    __tablename__ = "build_feature_effects"
    __table_args__ = (
        UniqueConstraint("feature_id", "effect_key", name="uq_build_feature_effect_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feature_id: Mapped[int] = mapped_column(
        ForeignKey("build_features.id", ondelete="CASCADE"), nullable=False, index=True
    )
    effect_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    effect_value: Mapped[float] = mapped_column(Float, nullable=False)

    feature: Mapped[BuildFeatureDefinition] = relationship(
        BuildFeatureDefinition, back_populates="effects"
    )

    @property
    def normalized_value(self) -> int | float:
        return int(self.effect_value) if self.effect_value.is_integer() else self.effect_value
