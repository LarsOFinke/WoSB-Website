from app.core.time import utc_now
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BuildVote(Base):
    __tablename__ = "build_votes"
    __table_args__ = (
        UniqueConstraint("build_id", "user_id", name="uq_build_votes_build_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    build_id: Mapped[int] = mapped_column(
        ForeignKey("builds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
