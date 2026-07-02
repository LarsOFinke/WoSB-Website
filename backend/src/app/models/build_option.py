from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BuildOption(Base):
    __tablename__ = "build_options"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effect_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progression_class: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    ship_class: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    min_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
