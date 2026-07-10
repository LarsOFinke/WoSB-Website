from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ForumPostAttachment(Base):
    __tablename__ = "forum_post_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    post: Mapped["ForumPost"] = relationship("ForumPost", back_populates="attachments")
    file: Mapped["StoredFile"] = relationship("StoredFile", lazy="joined")
