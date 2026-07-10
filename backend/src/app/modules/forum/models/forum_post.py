from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("forum_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    thread: Mapped["ForumThread"] = relationship("ForumThread", back_populates="posts")
    author: Mapped["User"] = relationship("User", lazy="joined")
    attachments: Mapped[list["ForumPostAttachment"]] = relationship(
        "ForumPostAttachment",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ForumPostAttachment.sort_order",
    )
