from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ForumThread(Base):
    __tablename__ = "forum_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="general", index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["User"] = relationship("User", lazy="joined")
    posts: Mapped[list["ForumPost"]] = relationship(
        "ForumPost",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ForumPost.created_at",
    )

    @property
    def reply_count(self) -> int:
        return max(len(self.posts) - 1, 0)

    @property
    def last_activity_at(self) -> datetime:
        if self.posts:
            return max(post.created_at for post in self.posts)
        return self.updated_at


# Compatibility exports: historically imported from app.modules.forum.models.forum.
from app.modules.forum.models.forum_post import ForumPost  # noqa: E402
from app.modules.forum.models.forum_post_attachment import ForumPostAttachment  # noqa: E402

__all__ = ["ForumThread", "ForumPost", "ForumPostAttachment"]
