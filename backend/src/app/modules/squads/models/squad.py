from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Squad(Base):
    __tablename__ = "squads"
    __table_args__ = (
        UniqueConstraint("fleet_id", "name", name="uq_squads_fleet_name"),
        UniqueConstraint("fleet_id", "slug", name="uq_squads_fleet_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fleet_id: Mapped[int] = mapped_column(ForeignKey("fleets.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    focus: Mapped[str | None] = mapped_column(String(160), nullable=True)
    max_members: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fleet: Mapped["Fleet"] = relationship("Fleet", lazy="joined")
    created_by: Mapped["User"] = relationship("User", lazy="joined")
    members: Mapped[list["SquadMember"]] = relationship(
        "SquadMember",
        back_populates="squad",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SquadMember.joined_at",
    )
