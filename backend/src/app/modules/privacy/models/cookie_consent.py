from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.accounts.models.user import User


class CookieConsentDecision(Base):
    """Append-only record of a visitor's cookie-category decision.

    ``consent_key`` is stored in a strictly necessary HttpOnly cookie. Keeping
    decisions append-only preserves an auditable history without duplicating a
    mutable "current state" table; the newest row is the active decision.
    """

    __tablename__ = "cookie_consent_decisions"
    __table_args__ = (
        Index("ix_cookie_consent_key_created", "consent_key", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consent_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    necessary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preferences: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    analytics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_media: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user: Mapped["User | None"] = relationship(lazy="joined")
