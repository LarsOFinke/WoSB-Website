from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import FLEET_LEADERSHIP_ROLES, FleetRole, MembershipStatus
from app.db.base import Base

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

    memberships: Mapped[list["FleetMembership"]] = relationship(
        "FleetMembership", back_populates="fleet", cascade="all, delete-orphan"
    )


# Compatibility export: historically imported from app.modules.fleet.models.fleet.
from app.modules.fleet.models.fleet_membership import FleetMembership  # noqa: E402

__all__ = [
    "Fleet",
    "FleetMembership",
    "FLEET_LEADERSHIP_ROLES",
    "FLEET_ROLE_MEMBER",
    "FLEET_ROLE_LIEUTENANT",
    "FLEET_ROLE_ADMIRAL",
    "FLEET_ROLES",
    "FLEET_MEMBER_PENDING",
    "FLEET_MEMBER_ACTIVE",
    "FLEET_MEMBER_INACTIVE",
    "FLEET_MEMBER_STATUSES",
]
