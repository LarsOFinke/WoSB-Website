from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BuildItemOptionSlotType(Base):
    __tablename__ = "build_item_option_slot_types"
    __table_args__ = (
        UniqueConstraint("option_id", "slot_type_id", name="uq_build_item_option_slot_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    option_id: Mapped[int] = mapped_column(
        ForeignKey("build_item_options.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slot_type_id: Mapped[int] = mapped_column(
        ForeignKey("weapon_slot_types.id", ondelete="CASCADE"), nullable=False, index=True
    )

    option: Mapped["BuildItemOption"] = relationship("BuildItemOption", back_populates="slot_type_links")
    slot_type: Mapped["WeaponSlotType"] = relationship("WeaponSlotType", back_populates="option_links", lazy="joined")
