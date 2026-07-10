from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.fleet.models.fleet import FLEET_MEMBER_PENDING, FLEET_ROLE_MEMBER


class FleetMembership(Base):
    __tablename__ = "fleet_memberships"
    __table_args__ = (
        UniqueConstraint("fleet_id", "user_id", name="uq_fleet_membership_user"),
        UniqueConstraint("user_id", name="uq_fleet_membership_single_user"),
        CheckConstraint("role in ('member', 'fleet_lieutenant', 'fleet_admiral')", name="ck_fleet_memberships_role"),
        CheckConstraint("status in ('pending', 'active', 'inactive')", name="ck_fleet_memberships_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fleet_id: Mapped[int] = mapped_column(ForeignKey("fleets.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default=FLEET_ROLE_MEMBER, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=FLEET_MEMBER_PENDING, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(240), nullable=True)
    preferred_ships: Mapped[str | None] = mapped_column(String(300), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    discord_handle: Mapped[str | None] = mapped_column(String(120), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fleet: Mapped["Fleet"] = relationship("Fleet", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="fleet_memberships")
