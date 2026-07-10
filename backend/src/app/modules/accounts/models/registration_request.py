from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

REGISTRATION_PENDING = "pending"
REGISTRATION_APPROVED = "approved"
REGISTRATION_REJECTED = "rejected"
REGISTRATION_STATUSES = {REGISTRATION_PENDING, REGISTRATION_APPROVED, REGISTRATION_REJECTED}


class RegistrationRequest(Base):
    """Staged signup data that must be reviewed before a user account exists."""

    __tablename__ = "registration_requests"
    __table_args__ = (
        CheckConstraint("status in ('pending', 'approved', 'rejected')", name="ck_registration_requests_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    external_fleet_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fleet_id: Mapped[int | None] = mapped_column(ForeignKey("fleets.id"), nullable=True, index=True)
    wants_fleet_membership: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fleet_application_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    fleet_availability: Mapped[str | None] = mapped_column(String(240), nullable=True)
    fleet_preferred_ships: Mapped[str | None] = mapped_column(String(300), nullable=True)
    fleet_timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fleet_discord_handle: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default=REGISTRATION_PENDING, index=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    fleet: Mapped["Fleet | None"] = relationship(lazy="selectin")
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_id], lazy="selectin")
    created_user: Mapped["User | None"] = relationship(foreign_keys=[created_user_id], lazy="selectin")
