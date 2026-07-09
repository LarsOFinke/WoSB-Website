from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

ROLE_USER = "user"
ROLE_MODERATOR = "moderator"
ROLE_ADMIN = "admin"
STAFF_ROLES = {ROLE_MODERATOR, ROLE_ADMIN}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=ROLE_USER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    fleet_memberships: Mapped[list["FleetMembership"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        return self.profile.display_name if self.profile and self.profile.display_name else self.username

    @display_name.setter
    def display_name(self, value: str) -> None:
        self._ensure_profile().display_name = (value or self.username).strip() or self.username

    @property
    def fleet_name(self) -> str | None:
        return self.profile.external_fleet_name if self.profile else None

    @fleet_name.setter
    def fleet_name(self, value: str | None) -> None:
        self._ensure_profile().external_fleet_name = value.strip() or None if isinstance(value, str) else None

    @property
    def fleet_id(self) -> int | None:
        memberships = sorted(
            self.fleet_memberships or [],
            key=lambda item: (item.status != "active", item.status != "pending", item.joined_at),
        )
        return memberships[0].fleet_id if memberships else None

    @property
    def preferred_focus(self) -> str | None:
        return self.profile.preferred_focus if self.profile else None

    @preferred_focus.setter
    def preferred_focus(self, value: str | None) -> None:
        self._ensure_profile().preferred_focus = value.strip() or None if isinstance(value, str) else None

    @property
    def note(self) -> str | None:
        return self.profile.note if self.profile else None

    @note.setter
    def note(self, value: str | None) -> None:
        self._ensure_profile().note = value.strip() or None if isinstance(value, str) else None

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_moderator(self) -> bool:
        return self.role == ROLE_MODERATOR

    @property
    def can_moderate(self) -> bool:
        return self.role in STAFF_ROLES

    def _ensure_profile(self) -> "UserProfile":
        from app.models.user_profile import UserProfile

        if self.profile is None:
            self.profile = UserProfile(display_name=self.username)
        return self.profile
