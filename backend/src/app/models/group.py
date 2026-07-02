from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.group_participant import GroupParticipant
    from app.models.ship import Ship
    from app.models.user import User


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # Optional preferred ship. The hard requirement is min_ship_rate; a preferred
    # ship is only a hint for players.
    ship_id: Mapped[int | None] = mapped_column(ForeignKey("ships.id"), index=True, nullable=True)
    ship_class_label: Mapped[str] = mapped_column(String(80), default="Beliebig", nullable=False)

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    focus: Mapped[str] = mapped_column(String(40), default="pve_general", index=True, nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    min_ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fleet_restriction: Mapped[str | None] = mapped_column(String(120), nullable=True)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(hours=24), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="groups")
    ship: Mapped["Ship | None"] = relationship(back_populates="groups")
    participants: Mapped[list["GroupParticipant"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="GroupParticipant.joined_at",
    )
