from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.fleet.models.fleet import FLEET_MEMBER_PENDING, FLEET_ROLE_MEMBER


class FleetMembershipShipPreference(Base):
    __tablename__ = "fleet_membership_ship_preferences"
    __table_args__ = (
        UniqueConstraint("fleet_membership_id", "ship_name", name="uq_fleet_membership_ship_preference"),
        CheckConstraint("sort_order >= 0", name="ck_fleet_membership_ship_preferences_sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fleet_membership_id: Mapped[int] = mapped_column(
        ForeignKey("fleet_memberships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ship_name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    membership: Mapped["FleetMembership"] = relationship("FleetMembership", back_populates="ship_preferences")


class FleetMembership(Base):
    __tablename__ = "fleet_memberships"
    __table_args__ = (
        UniqueConstraint("fleet_id", "user_id", name="uq_fleet_membership_user"),
        UniqueConstraint("user_id", name="uq_fleet_membership_single_user"),
        CheckConstraint("status in ('pending', 'active', 'inactive')", name="ck_fleet_memberships_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fleet_id: Mapped[int] = mapped_column(ForeignKey("fleets.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    fleet_role_id: Mapped[int] = mapped_column(ForeignKey("fleet_roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=FLEET_MEMBER_PENDING, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(240), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    discord_handle: Mapped[str | None] = mapped_column(String(120), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fleet: Mapped["Fleet"] = relationship("Fleet", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="fleet_memberships")
    fleet_role: Mapped["FleetRoleDefinition"] = relationship(
        "FleetRoleDefinition", back_populates="memberships", lazy="joined"
    )
    ship_preferences: Mapped[list[FleetMembershipShipPreference]] = relationship(
        FleetMembershipShipPreference,
        back_populates="membership",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by=FleetMembershipShipPreference.sort_order,
    )

    @property
    def role(self) -> str:
        return self.fleet_role.code if self.fleet_role is not None else FLEET_ROLE_MEMBER

    @property
    def role_rank(self) -> int:
        return int(self.fleet_role.rank if self.fleet_role is not None else 0)

    @property
    def preferred_ships(self) -> str | None:
        names = [row.ship_name for row in self.ship_preferences]
        return ", ".join(names) if names else None

    def set_preferred_ships(self, value: str | None) -> None:
        seen: set[str] = set()
        names: list[str] = []
        for raw in (value or "").replace(";", ",").split(","):
            name = raw.strip()
            key = name.casefold()
            if not name or key in seen:
                continue
            seen.add(key)
            names.append(name)
        self.ship_preferences[:] = [
            FleetMembershipShipPreference(ship_name=name, sort_order=index * 10)
            for index, name in enumerate(names, start=1)
        ]
