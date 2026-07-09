from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

FLEET_ROLE_MEMBER = "member"
FLEET_ROLE_LIEUTENANT = "fleet_lieutenant"
FLEET_ROLE_ADMIRAL = "fleet_admiral"
FLEET_LEADERSHIP_ROLES = {FLEET_ROLE_ADMIRAL, FLEET_ROLE_LIEUTENANT}
FLEET_ROLES = {FLEET_ROLE_MEMBER, FLEET_ROLE_LIEUTENANT, FLEET_ROLE_ADMIRAL}

FLEET_MEMBER_PENDING = "pending"
FLEET_MEMBER_ACTIVE = "active"
FLEET_MEMBER_INACTIVE = "inactive"
FLEET_MEMBER_STATUSES = {FLEET_MEMBER_PENDING, FLEET_MEMBER_ACTIVE, FLEET_MEMBER_INACTIVE}


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
    __table_args__ = (UniqueConstraint("fleet_id", "user_id", name="uq_fleet_membership_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fleet_id: Mapped[int] = mapped_column(ForeignKey("fleets.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default=FLEET_ROLE_MEMBER, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=FLEET_MEMBER_PENDING, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fleet: Mapped[Fleet] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="fleet_memberships")
