from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class RaidHelperProfile(Base):
    __tablename__ = "raid_helper_profiles"
    __table_args__ = (
        CheckConstraint(
            "authorization_mode IN ('authorization', 'bearer', 'x-api-key')",
            name="ck_raid_helper_profile_authorization_mode",
        ),
        UniqueConstraint("name", name="uq_raid_helper_profiles_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    server_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_base_url: Mapped[str] = mapped_column(String(200), nullable=False, default="https://raid-helper.xyz/api/v4")
    authorization_mode: Mapped[str] = mapped_column(String(24), nullable=False, default="authorization")
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="Europe/Berlin")
    default_leader_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_by_username: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    destinations: Mapped[list["RaidHelperDestination"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    templates: Mapped[list["RaidHelperTemplate"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class RaidHelperDestination(Base):
    __tablename__ = "raid_helper_destinations"
    __table_args__ = (
        CheckConstraint("scope_type IN ('fleet', 'squad')", name="ck_raid_helper_destination_scope"),
        CheckConstraint(
            "(scope_type = 'fleet' AND squad_id IS NULL) OR (scope_type = 'squad' AND squad_id IS NOT NULL)",
            name="ck_raid_helper_destination_scope_target",
        ),
        Index("ix_raid_helper_destinations_scope", "scope_type", "squad_id", "is_active"),
        Index(
            "uq_raid_helper_destinations_fleet_channel",
            "profile_id",
            "channel_id",
            unique=True,
            postgresql_where=text("scope_type = 'fleet'"),
            sqlite_where=text("scope_type = 'fleet'"),
        ),
        Index(
            "uq_raid_helper_destinations_squad_channel",
            "profile_id",
            "channel_id",
            "squad_id",
            unique=True,
            postgresql_where=text("scope_type = 'squad'"),
            sqlite_where=text("scope_type = 'squad'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("raid_helper_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(16), nullable=False)
    squad_id: Mapped[int | None] = mapped_column(ForeignKey("squads.id", ondelete="CASCADE"), nullable=True, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    profile: Mapped[RaidHelperProfile] = relationship(back_populates="destinations", lazy="joined")
    squad: Mapped["Squad | None"] = relationship(lazy="joined")
    categories: Mapped[list["RaidHelperDestinationCategory"]] = relationship(back_populates="destination", cascade="all, delete-orphan")


class RaidHelperDestinationCategory(Base):
    __tablename__ = "raid_helper_destination_categories"
    destination_id: Mapped[int] = mapped_column(ForeignKey("raid_helper_destinations.id", ondelete="CASCADE"), primary_key=True)
    category: Mapped[str] = mapped_column(String(80), primary_key=True)
    destination: Mapped[RaidHelperDestination] = relationship(back_populates="categories")


class RaidHelperTemplate(Base):
    __tablename__ = "raid_helper_templates"
    __table_args__ = (
        CheckConstraint("scope_type IN ('both', 'fleet', 'squad')", name="ck_raid_helper_template_scope"),
        UniqueConstraint("profile_id", "name", name="uq_raid_helper_template_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("raid_helper_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    raid_template_id: Mapped[str] = mapped_column(String(80), nullable=False, default="Standard")
    scope_type: Mapped[str] = mapped_column(String(16), nullable=False, default="both")
    title_template: Mapped[str] = mapped_column(String(300), nullable=False, default="{{event.title}}")
    description_template: Mapped[str] = mapped_column(Text, nullable=False, default="{{event.description}}")
    announcement_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    payload_template_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    profile: Mapped[RaidHelperProfile] = relationship(back_populates="templates", lazy="joined")
    categories: Mapped[list["RaidHelperTemplateCategory"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class RaidHelperTemplateCategory(Base):
    __tablename__ = "raid_helper_template_categories"
    template_id: Mapped[int] = mapped_column(ForeignKey("raid_helper_templates.id", ondelete="CASCADE"), primary_key=True)
    category: Mapped[str] = mapped_column(String(80), primary_key=True)
    template: Mapped[RaidHelperTemplate] = relationship(back_populates="categories")


class RaidHelperEventLink(Base):
    __tablename__ = "raid_helper_event_links"
    __table_args__ = (
        UniqueConstraint("event_id", "destination_id", name="uq_raid_helper_event_destination"),
        Index("ix_raid_helper_event_links_status_updated", "status", "updated_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("fleet_events.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("raid_helper_destinations.id", ondelete="RESTRICT"), nullable=False, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("raid_helper_templates.id", ondelete="RESTRICT"), nullable=False, index=True)
    leader_id_override: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued")
    last_operation: Mapped[str] = mapped_column(String(16), nullable=False, default="create")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    event: Mapped["FleetEvent"] = relationship(back_populates="raid_helper_links", lazy="joined")
    destination: Mapped[RaidHelperDestination] = relationship(lazy="joined")
    template: Mapped[RaidHelperTemplate] = relationship(lazy="joined")
