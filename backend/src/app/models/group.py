from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.user import User

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    focus: Mapped[str] = mapped_column(String(80), nullable=False, default="pve_general", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_members: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    min_ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_guests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fleet_restriction: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=GROUP_STATUS_OPEN, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(hours=DEFAULT_GROUP_LIFETIME_HOURS),
        index=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    owner: Mapped[User] = relationship(lazy="joined")
    members: Mapped[list["GroupMember"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="GroupMember.joined_at",
    )

    @property
    def active_members_count(self) -> int:
        return sum(1 for member in self.members if member.is_active)

    @property
    def spots_left(self) -> int:
        return max(self.max_members - self.active_members_count, 0)

    @property
    def is_joinable(self) -> bool:
        return self.status == GROUP_STATUS_OPEN and self.spots_left > 0


class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    fleet_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ship_id: Mapped[int | None] = mapped_column(ForeignKey("ships.id"), nullable=True, index=True)
    ship_name: Mapped[str | None] = mapped_column(String(140), nullable=True)
    ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User | None] = relationship(lazy="joined")
    ship: Mapped["Ship | None"] = relationship("Ship", lazy="joined")
