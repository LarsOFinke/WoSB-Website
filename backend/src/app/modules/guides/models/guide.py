from __future__ import annotations

from app.core.time import utc_now

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="general", index=True)
    summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    owner: Mapped["User"] = relationship("User", lazy="joined")
    attachments: Mapped[list["GuideAttachment"]] = relationship(
        "GuideAttachment",
        back_populates="guide",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="GuideAttachment.sort_order",
    )
    build_references: Mapped[list["GuideBuildReference"]] = relationship(
        "GuideBuildReference",
        back_populates="guide",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="GuideBuildReference.sort_order",
    )


# Compatibility exports: historically imported from app.modules.guides.models.guide.
from app.modules.guides.models.guide_attachment import GuideAttachment  # noqa: E402
from app.modules.guides.models.guide_build_reference import GuideBuildReference  # noqa: E402

__all__ = ["Guide", "GuideAttachment", "GuideBuildReference"]
