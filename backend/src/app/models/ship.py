from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.build import Build
    from app.models.group import Group
    from app.models.profile import Profile


class Ship(Base):
    __tablename__ = "ships"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    rate: Mapped[str] = mapped_column(String(8), index=True, nullable=False)
    progression_class: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    ship_class: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    school: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    is_legend: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_early_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    durability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    agility: Mapped[int | None] = mapped_column(Integer, nullable=True)
    armor: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    hold_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crew: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hull_size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    displacement_tons: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    groups: Mapped[list[Group]] = relationship(back_populates="ship")
    builds: Mapped[list[Build]] = relationship(back_populates="ship")
    preferred_by_profiles: Mapped[list[Profile]] = relationship(back_populates="preferred_ship")
