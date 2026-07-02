from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.build import Build
    from app.models.group import Group
    from app.models.group_participant import GroupParticipant
    from app.models.profile import Profile


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="member", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    profile: Mapped[Profile] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    groups: Mapped[list[Group]] = relationship(back_populates="owner")
    builds: Mapped[list[Build]] = relationship(back_populates="author")
    participations: Mapped[list[GroupParticipant]] = relationship(back_populates="user")
