from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import FLEET_LEADERSHIP_ROLES, FleetRole, MembershipStatus
from app.db.session import Base

FLEET_ROLE_MEMBER = FleetRole.MEMBER.value
FLEET_ROLE_LIEUTENANT = FleetRole.LIEUTENANT.value
FLEET_ROLE_ADMIRAL = FleetRole.ADMIRAL.value
FLEET_ROLES = {role.value for role in FleetRole}

FLEET_MEMBER_PENDING = MembershipStatus.PENDING.value
FLEET_MEMBER_ACTIVE = MembershipStatus.ACTIVE.value
FLEET_MEMBER_INACTIVE = MembershipStatus.INACTIVE.value
FLEET_MEMBER_STATUSES = {status.value for status in MembershipStatus}


class Fleet(Base):
    __tablename__ = "fleets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    focus: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    standing_orders: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships: Mapped[list["FleetMembership"]] = relationship(back_populates="fleet", cascade="all, delete-orphan")


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

    fleet: Mapped[Fleet] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="fleet_memberships")
