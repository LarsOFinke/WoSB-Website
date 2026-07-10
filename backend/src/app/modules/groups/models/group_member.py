from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        CheckConstraint("ship_rate is null or (ship_rate >= 1 and ship_rate <= 7)", name="ck_group_members_ship_rate"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    fleet_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ship_id: Mapped[int | None] = mapped_column(ForeignKey("ships.id"), nullable=True, index=True)
    build_id: Mapped[int | None] = mapped_column(ForeignKey("builds.id"), nullable=True, index=True)
    ship_name: Mapped[str | None] = mapped_column(String(140), nullable=True)
    ship_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User | None"] = relationship("User", lazy="joined")
    ship: Mapped["Ship | None"] = relationship("Ship", lazy="joined")
    build: Mapped["Build | None"] = relationship("Build", lazy="joined")
