from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProfile(Base):
    """Mutable public profile data for a user.

    Authentication/account state stays on ``users``. Public profile fields live
    here so profile notes do not bloat the auth table. The user's official fleet
    connection is centralized via ``primary_fleet_membership_id``: that single
    pointer references the fleet_memberships row that drives profile display,
    registration claims and later fleet-leadership approvals.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    external_fleet_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_fleet_membership_id: Mapped[int | None] = mapped_column(
        ForeignKey("fleet_memberships.id", ondelete="SET NULL"), nullable=True, index=True
    )
    preferred_focus: Mapped[str | None] = mapped_column(String(80), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")
    primary_fleet_membership: Mapped["FleetMembership | None"] = relationship(
        foreign_keys=[primary_fleet_membership_id], lazy="selectin"
    )
