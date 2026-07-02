from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ship import Ship
    from app.models.user import User


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    main_role: Mapped[str] = mapped_column(String(80), default="Kapitän", nullable=False)
    fleet_name: Mapped[str] = mapped_column(String(100), default="Ohne Flotte", nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    preferred_ship_id: Mapped[int | None] = mapped_column(ForeignKey("ships.id"), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")
    preferred_ship: Mapped[Ship | None] = relationship(back_populates="preferred_by_profiles")
