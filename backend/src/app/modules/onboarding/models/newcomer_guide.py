from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NewcomerGuidePage(Base):
    __tablename__ = "newcomer_guide_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    intro: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    updated_by: Mapped["User | None"] = relationship("User", lazy="joined")
    blocks: Mapped[list["NewcomerGuideBlock"]] = relationship(
        "NewcomerGuideBlock",
        back_populates="page",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="NewcomerGuideBlock.sort_order",
    )


class NewcomerGuideBlock(Base):
    __tablename__ = "newcomer_guide_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    page_id: Mapped[int] = mapped_column(
        ForeignKey("newcomer_guide_pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    block_type: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    page: Mapped[NewcomerGuidePage] = relationship("NewcomerGuidePage", back_populates="blocks")
    resources: Mapped[list["NewcomerGuideResource"]] = relationship(
        "NewcomerGuideResource",
        back_populates="block",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="NewcomerGuideResource.sort_order",
    )


class NewcomerGuideResource(Base):
    __tablename__ = "newcomer_guide_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    block_id: Mapped[int] = mapped_column(
        ForeignKey("newcomer_guide_blocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(String(24), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label: Mapped[str | None] = mapped_column(String(180), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    block: Mapped[NewcomerGuideBlock] = relationship("NewcomerGuideBlock", back_populates="resources")
