from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ship import Ship
    from app.models.user import User


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    ship_id: Mapped[int | None] = mapped_column(ForeignKey("ships.id"), index=True, nullable=True)
    ship_class_label: Mapped[str] = mapped_column(String(80), default="Beliebig", nullable=False)

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    purpose: Mapped[str] = mapped_column(String(80), default="Allround", nullable=False)
    build_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cannon_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    weapon_bow_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    weapon_port_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    weapon_starboard_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    weapon_stern_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sail_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    upgrade_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    crew_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crew_gunnery: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crew_sailing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crew_repair: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crew_boarding: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crew_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    special_crew_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cargo_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ammunition_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    consumable_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tactics: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    author: Mapped[User] = relationship(back_populates="builds")
    ship: Mapped[Ship | None] = relationship(back_populates="builds")
