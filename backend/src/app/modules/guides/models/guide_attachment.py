from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GuideAttachment(Base):
    __tablename__ = "guide_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    guide: Mapped["Guide"] = relationship("Guide", back_populates="attachments")
    file: Mapped["StoredFile"] = relationship("StoredFile", lazy="joined")
