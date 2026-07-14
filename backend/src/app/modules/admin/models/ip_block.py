from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class IpBlock(Base):
    """Staff-managed exact-IP access block with retained unblock history."""

    __tablename__ = "ip_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(240), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_username: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    unblocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    unblocked_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    unblocked_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    unblock_reason: Mapped[str | None] = mapped_column(String(240), nullable=True)

    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id], lazy="joined")
    unblocked_by: Mapped["User | None"] = relationship("User", foreign_keys=[unblocked_by_user_id], lazy="joined")
