from app.core.time import utc_now
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BuildSlot(Base):
    __tablename__ = "build_slots"
    __table_args__ = (
        UniqueConstraint("build_id", "slot_type", "slot_index", name="uq_build_slot_position"),
        CheckConstraint("slot_index >= 0", name="ck_build_slots_slot_index"),
        CheckConstraint("quantity is null or quantity >= 1", name="ck_build_slots_quantity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    build_id: Mapped[int] = mapped_column(
        ForeignKey("builds.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slot_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    option_id: Mapped[int] = mapped_column(
        ForeignKey("build_item_options.id"), nullable=False, index=True
    )
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    option: Mapped["BuildItemOption"] = relationship(lazy="joined")
