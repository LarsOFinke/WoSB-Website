from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BuildFileAttachment(Base):
    __tablename__ = "build_file_attachments"
    __table_args__ = (UniqueConstraint("build_id", "file_id", name="uq_build_file_attachment"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    build_id: Mapped[int] = mapped_column(
        ForeignKey("builds.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[int] = mapped_column(
        ForeignKey("stored_files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    file: Mapped["StoredFile"] = relationship("StoredFile", lazy="joined")
