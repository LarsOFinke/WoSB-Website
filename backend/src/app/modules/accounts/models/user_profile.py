from __future__ import annotations

from app.core.time import utc_now

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProfileShipPreference(Base):
    __tablename__ = "user_profile_ship_preferences"
    __table_args__ = (UniqueConstraint("user_id", "ship_id", name="uq_user_profile_ship_preference"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profile: Mapped["UserProfile"] = relationship(back_populates="ship_preferences")
    ship: Mapped["Ship"] = relationship(lazy="joined")


class UserProfileRolePreference(Base):
    __tablename__ = "user_profile_role_preferences"
    __table_args__ = (UniqueConstraint("user_id", "fleet_role_id", name="uq_user_profile_role_preference"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)
    fleet_role_id: Mapped[int] = mapped_column(ForeignKey("fleet_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profile: Mapped["UserProfile"] = relationship(back_populates="role_preferences")
    fleet_role: Mapped["FleetRoleDefinition"] = relationship(lazy="joined")


class UserProfile(Base):
    """User-owned optional directory data, independent from fleet membership."""

    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    external_fleet_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    preferred_focus: Mapped[str | None] = mapped_column(String(80), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(240), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    discord_handle: Mapped[str | None] = mapped_column(String(120), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship(back_populates="profile")
    ship_preferences: Mapped[list[UserProfileShipPreference]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin", order_by=UserProfileShipPreference.sort_order
    )
    role_preferences: Mapped[list[UserProfileRolePreference]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin", order_by=UserProfileRolePreference.sort_order
    )
