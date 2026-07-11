from __future__ import annotations

from app.core.time import utc_now

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SiteRoleDefinition(Base):
    __tablename__ = "site_roles"
    __table_args__ = (CheckConstraint("rank >= 0", name="ck_site_roles_rank"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_manage_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)

    users: Mapped[list["User"]] = relationship("User", back_populates="site_role")


class FleetRoleDefinition(Base):
    __tablename__ = "fleet_roles"
    __table_args__ = (CheckConstraint("rank >= 0", name="ck_fleet_roles_rank"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_leadership: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    can_manage_fleet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_manage_members: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)

    memberships: Mapped[list["FleetMembership"]] = relationship("FleetMembership", back_populates="fleet_role")


class SquadRoleDefinition(Base):
    __tablename__ = "squad_roles"
    __table_args__ = (CheckConstraint("rank >= 0", name="ck_squad_roles_rank"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    can_manage_roster: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_manage_events: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)

    members: Mapped[list["SquadMember"]] = relationship("SquadMember", back_populates="squad_role")
