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
        CheckConstraint("status in ('pending', 'active', 'inactive')", name="ck_fleet_memberships_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fleet_id: Mapped[int] = mapped_column(ForeignKey("fleets.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    fleet_role_id: Mapped[int] = mapped_column(ForeignKey("fleet_roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=FLEET_MEMBER_PENDING, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fleet: Mapped["Fleet"] = relationship("Fleet", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="fleet_memberships")
    fleet_role: Mapped["FleetRoleDefinition"] = relationship(
        "FleetRoleDefinition", back_populates="memberships", lazy="joined"
    )

    @property
    def role(self) -> str:
        return self.fleet_role.code if self.fleet_role is not None else FLEET_ROLE_MEMBER

    @property
    def role_rank(self) -> int:
        return int(self.fleet_role.rank if self.fleet_role is not None else 0)

    @property
    def availability(self) -> str | None:
        return self.user.profile.availability if self.user and self.user.profile else None

    @property
    def timezone(self) -> str | None:
        return self.user.profile.timezone if self.user and self.user.profile else None

    @property
    def discord_handle(self) -> str | None:
        return self.user.profile.discord_handle if self.user and self.user.profile else None

    @property
    def preferred_ships(self) -> str | None:
        if not self.user or not self.user.profile:
            return None
        names = [row.ship.name for row in self.user.profile.ship_preferences if row.ship]
        return ", ".join(names) if names else None

    @property
    def preferred_roles(self) -> str | None:
        if not self.user or not self.user.profile:
            return None
        names = [row.fleet_role.label for row in self.user.profile.role_preferences if row.fleet_role]
        return ", ".join(names) if names else None
