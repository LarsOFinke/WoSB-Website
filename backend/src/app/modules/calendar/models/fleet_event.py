from app.core.time import utc_now
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FleetEvent(Base):
    __tablename__ = "fleet_events"
    __table_args__ = (
        CheckConstraint("end_at >= start_at", name="ck_fleet_events_time_range"),
        Index("ix_fleet_events_active_start", "is_cancelled", "start_at", "id"),
        Index("ix_fleet_events_squad_active_start", "squad_id", "is_cancelled", "start_at", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="other", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    squad_id: Mapped[int | None] = mapped_column(ForeignKey("squads.id", ondelete="SET NULL"), nullable=True, index=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    raid_helper_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    owner: Mapped["User"] = relationship("User", lazy="joined")
    squad: Mapped["Squad | None"] = relationship("Squad", lazy="joined")
    raid_helper_links: Mapped[list["RaidHelperEventLink"]] = relationship(cascade="all, delete-orphan", passive_deletes=True, lazy="selectin")
