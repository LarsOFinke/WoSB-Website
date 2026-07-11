from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import OFFICIAL_FLEET_PROFILE_STATUSES, SiteRole
from app.db.base import Base

ROLE_USER = SiteRole.USER.value
ROLE_MODERATOR = SiteRole.MODERATOR.value
ROLE_ADMIN = SiteRole.ADMIN.value


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    site_role_id: Mapped[int] = mapped_column(ForeignKey("site_roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    site_role: Mapped["SiteRoleDefinition"] = relationship(
        "SiteRoleDefinition", back_populates="users", lazy="joined"
    )
    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    fleet_memberships: Mapped[list["FleetMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", foreign_keys="FleetMembership.user_id"
    )

    @property
    def role(self) -> str:
        return self.site_role.code if self.site_role is not None else ROLE_USER

    @property
    def role_rank(self) -> int:
        return int(self.site_role.rank if self.site_role is not None else 0)

    @property
    def display_name(self) -> str:
        return self.profile.display_name if self.profile and self.profile.display_name else self.username

    @display_name.setter
    def display_name(self, value: str) -> None:
        self._ensure_profile().display_name = (value or self.username).strip() or self.username

    @property
    def primary_fleet_membership(self) -> "FleetMembership | None":
        candidates = [
            membership
            for membership in self.fleet_memberships
            if membership.status in OFFICIAL_FLEET_PROFILE_STATUSES
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda membership: (
                membership.status != "active",
                -membership.role_rank,
                membership.id,
            ),
        )[0]

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
    def availability(self) -> str | None:
        return self.profile.availability if self.profile else None

    @property
    def timezone(self) -> str | None:
        return self.profile.timezone if self.profile else None

    @property
    def discord_handle(self) -> str | None:
        return self.profile.discord_handle if self.profile else None

    @property
    def preferred_ship_ids(self) -> list[int]:
        return [row.ship_id for row in self.profile.ship_preferences] if self.profile else []

    @property
    def preferred_role_ids(self) -> list[int]:
        return [row.fleet_role_id for row in self.profile.role_preferences] if self.profile else []

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
        return bool(self.site_role and self.site_role.is_staff)

    @property
    def can_manage_system(self) -> bool:
        return bool(self.site_role and self.site_role.can_manage_system)

    def _ensure_profile(self) -> "UserProfile":
        from app.modules.accounts.models.user_profile import UserProfile

        if self.profile is None:
            self.profile = UserProfile(display_name=self.username)
        return self.profile
