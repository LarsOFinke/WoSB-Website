from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class DataSubjectRequest(Base):
    __tablename__ = "data_subject_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    request_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    handled_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    subject: Mapped["User"] = relationship("User", foreign_keys=[subject_user_id])
    handled_by: Mapped["User | None"] = relationship("User", foreign_keys=[handled_by_user_id])
