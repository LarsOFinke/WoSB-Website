from app.core.time import utc_now
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

REGISTRATION_PENDING = "pending"
REGISTRATION_APPROVED = "approved"
REGISTRATION_REJECTED = "rejected"
REGISTRATION_STATUSES = {REGISTRATION_PENDING, REGISTRATION_APPROVED, REGISTRATION_REJECTED}


class RegistrationRequest(Base):
    """Staged portal-account data reviewed before a user account exists.

    An optional fleet application is stored here until the account is approved.
    The actual fleet membership is created transactionally with the user.
    """

    __tablename__ = "registration_requests"
    __table_args__ = (
        CheckConstraint("status in ('pending', 'approved', 'rejected')", name="ck_registration_requests_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    wants_fleet_membership: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fleet_id: Mapped[int | None] = mapped_column(ForeignKey("fleets.id", ondelete="SET NULL"), nullable=True, index=True)
    fleet_application_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default=REGISTRATION_PENDING, index=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_id], lazy="selectin")
    created_user: Mapped["User | None"] = relationship(foreign_keys=[created_user_id], lazy="selectin")
    requested_fleet: Mapped["Fleet | None"] = relationship(foreign_keys=[fleet_id], lazy="selectin")
