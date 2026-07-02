from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.ship import Ship
    from app.models.user import User


class GroupParticipant(Base):
    __tablename__ = "group_participants"
    __table_args__ = (
        UniqueConstraint("group_id", "display_name", name="uq_group_participant_display_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="member", index=True, nullable=False)
    participant_role: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Kept for old local developer DBs; new anonymous tokens are stored only as hash.
    join_token: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)
    anonymous_edit_token_hash: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)

    fleet_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ship_id: Mapped[int | None] = mapped_column(ForeignKey("ships.id"), index=True, nullable=True)
    custom_ship_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    custom_ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    group: Mapped["Group"] = relationship(back_populates="participants")
    user: Mapped["User | None"] = relationship(back_populates="participations")
    ship: Mapped["Ship | None"] = relationship()
