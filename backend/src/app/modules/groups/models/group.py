from __future__ import annotations

from app.core.time import utc_now

from datetime import datetime, timedelta

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.accounts.models.user import User

GROUP_STATUS_OPEN = "open"
GROUP_STATUS_FULL = "full"
GROUP_STATUS_CLOSED = "closed"
GROUP_STATUSES = {GROUP_STATUS_OPEN, GROUP_STATUS_FULL, GROUP_STATUS_CLOSED}

GROUP_FOCUS_VALUES = {
    "pve_farming",
    "pve_imp_hunting",
    "pve_general",
    "pvp_open_world",
    "pvp_arena",
    "pvp_general",
    "trading",
    "other",
}

DEFAULT_GROUP_LIFETIME_HOURS = 24


class Group(Base):
    __tablename__ = "groups"
    __table_args__ = (
        CheckConstraint("status in ('open', 'full', 'closed')", name="ck_groups_status"),
        CheckConstraint("max_members >= 2 and max_members <= 50", name="ck_groups_max_members"),
        CheckConstraint("min_ship_rate is null or (min_ship_rate >= 1 and min_ship_rate <= 7)", name="ck_groups_min_ship_rate"),
        CheckConstraint("max_ship_rate is null or (max_ship_rate >= 1 and max_ship_rate <= 7)", name="ck_groups_max_ship_rate"),
        CheckConstraint("scheduled_end_at is null or scheduled_start_at is null or scheduled_end_at > scheduled_start_at", name="ck_groups_schedule_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    focus: Mapped[str] = mapped_column(String(80), nullable=False, default="pve_general", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expectations: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    scheduled_start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    scheduled_end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_members: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    min_ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_guests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fleet_restriction: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=GROUP_STATUS_OPEN, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: utc_now() + timedelta(hours=DEFAULT_GROUP_LIFETIME_HOURS),
        index=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    owner: Mapped[User] = relationship(lazy="joined")
    members: Mapped[list["GroupMember"]] = relationship(
        "GroupMember",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="GroupMember.joined_at",
    )

    @property
    def active_members_count(self) -> int:
        return sum(1 for member in self.members if member.is_active)

    @property
    def spots_left(self) -> int:
        return max(0, self.max_members - self.active_members_count)

    @property
    def is_joinable(self) -> bool:
        return self.status == GROUP_STATUS_OPEN and self.spots_left > 0 and self.expires_at > utc_now()


# Compatibility export: historically imported from app.modules.groups.models.group.
from app.modules.groups.models.group_member import GroupMember  # noqa: E402

__all__ = [
    "Group",
    "GroupMember",
    "GROUP_STATUS_OPEN",
    "GROUP_STATUS_FULL",
    "GROUP_STATUS_CLOSED",
    "GROUP_STATUSES",
    "GROUP_FOCUS_VALUES",
    "DEFAULT_GROUP_LIFETIME_HOURS",
]
