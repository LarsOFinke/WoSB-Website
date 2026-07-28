from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.builds.models.build import Build


class BuildClassification(Base):
    """Normalized, filterable discovery tag assigned to a build."""

    __tablename__ = "build_classifications"
    __table_args__ = (
        Index("ix_build_classifications_tag_build_id", "tag", "build_id"),
    )

    build_id: Mapped[int] = mapped_column(
        ForeignKey("builds.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(40), primary_key=True)

    build: Mapped["Build"] = relationship(back_populates="classifications")
