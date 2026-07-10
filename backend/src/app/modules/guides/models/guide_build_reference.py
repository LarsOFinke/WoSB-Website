from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class GuideBuildReference(Base):
    __tablename__ = "guide_build_references"
    __table_args__ = (UniqueConstraint("guide_id", "build_id", name="uq_guide_build_reference"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), nullable=False, index=True)
    build_id: Mapped[int] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    guide: Mapped["Guide"] = relationship("Guide", back_populates="build_references")
    build: Mapped["Build"] = relationship("Build", lazy="joined")
