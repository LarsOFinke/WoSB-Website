from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

REGISTRATION_PENDING = "pending"
REGISTRATION_APPROVED = "approved"
REGISTRATION_REJECTED = "rejected"
REGISTRATION_STATUSES = {REGISTRATION_PENDING, REGISTRATION_APPROVED, REGISTRATION_REJECTED}


class RegistrationRequest(Base):
    """Staged portal-account data reviewed before a user account exists.

    Fleet applications are a separate authenticated workflow and therefore do
    not belong to the registration-request relation.
    """

    __tablename__ = "registration_requests"
    __table_args__ = (
        CheckConstraint("status in ('pending', 'approved', 'rejected')", name="ck_registration_requests_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default=REGISTRATION_PENDING, index=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_id], lazy="selectin")
    created_user: Mapped["User | None"] = relationship(foreign_keys=[created_user_id], lazy="selectin")
