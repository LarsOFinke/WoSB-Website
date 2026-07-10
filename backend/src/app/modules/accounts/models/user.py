from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import OFFICIAL_FLEET_PROFILE_STATUSES, STAFF_ROLES, SiteRole
from app.db.session import Base

ROLE_USER = SiteRole.USER.value
ROLE_MODERATOR = SiteRole.MODERATOR.value
ROLE_ADMIN = SiteRole.ADMIN.value


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role in ('user', 'moderator', 'admin')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=ROLE_USER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    fleet_memberships: Mapped[list["FleetMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", foreign_keys="FleetMembership.user_id"
    )

    @property
    def display_name(self) -> str:
        return self.profile.display_name if self.profile and self.profile.display_name else self.username

    @display_name.setter
    def display_name(self, value: str) -> None:
        self._ensure_profile().display_name = (value or self.username).strip() or self.username

    @property
    def primary_fleet_membership(self) -> "FleetMembership | None":
        if self.profile is None:
            return None
        membership = self.profile.primary_fleet_membership
        if membership is None or membership.user_id != self.id or membership.status not in OFFICIAL_FLEET_PROFILE_STATUSES:
            return None
        return membership

    @property
    def fleet_id(self) -> int | None:
        membership = self.primary_fleet_membership
        return membership.fleet_id if membership else None

    @property
    def fleet_name(self) -> str | None:
        membership = self.primary_fleet_membership
        if membership and membership.fleet:
            return membership.fleet.name
        return self.profile.external_fleet_name if self.profile else None

    @fleet_name.setter
    def fleet_name(self, value: str | None) -> None:
        self._ensure_profile().external_fleet_name = value.strip() or None if isinstance(value, str) else None

    @property
    def fleet_membership_id(self) -> int | None:
        membership = self.primary_fleet_membership
        return membership.id if membership else None

    @property
    def fleet_membership_status(self) -> str | None:
        membership = self.primary_fleet_membership
        return membership.status if membership else None

    @property
    def fleet_membership_role(self) -> str | None:
        membership = self.primary_fleet_membership
        return membership.role if membership else None

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
        from app.modules.accounts.models.user_profile import UserProfile

        if self.profile is None:
            self.profile = UserProfile(display_name=self.username)
        return self.profile
