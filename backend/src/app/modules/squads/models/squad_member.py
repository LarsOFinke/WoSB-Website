from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SQUAD_ROLE_MEMBER = "member"
SQUAD_ROLE_OFFICER = "officer"
SQUAD_ROLE_LEADER = "leader"
SQUAD_ROLES = {SQUAD_ROLE_MEMBER, SQUAD_ROLE_OFFICER, SQUAD_ROLE_LEADER}
SQUAD_MANAGEMENT_ROLES = {SQUAD_ROLE_OFFICER, SQUAD_ROLE_LEADER}


class SquadMember(Base):
    __tablename__ = "squad_members"
    __table_args__ = (
        UniqueConstraint("squad_id", "fleet_membership_id", name="uq_squad_members_membership"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id", ondelete="CASCADE"), nullable=False, index=True)
    fleet_membership_id: Mapped[int] = mapped_column(
        ForeignKey("fleet_memberships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    squad_role_id: Mapped[int] = mapped_column(ForeignKey("squad_roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    squad: Mapped["Squad"] = relationship("Squad", back_populates="members")
    fleet_membership: Mapped["FleetMembership"] = relationship("FleetMembership", lazy="joined")
    squad_role: Mapped["SquadRoleDefinition"] = relationship(
        "SquadRoleDefinition", back_populates="members", lazy="joined"
    )

    @property
    def role(self) -> str:
        return self.squad_role.code if self.squad_role is not None else SQUAD_ROLE_MEMBER

    @property
    def role_rank(self) -> int:
        return int(self.squad_role.rank if self.squad_role is not None else 0)
