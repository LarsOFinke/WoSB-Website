from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
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


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("forum_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    thread: Mapped[ForumThread] = relationship(back_populates="posts")
    author: Mapped["User"] = relationship("User", lazy="joined")
    attachments: Mapped[list["ForumPostAttachment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ForumPostAttachment.sort_order",
    )


class ForumPostAttachment(Base):
    __tablename__ = "forum_post_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    post: Mapped[ForumPost] = relationship(back_populates="attachments")
    file: Mapped["StoredFile"] = relationship(lazy="joined")
