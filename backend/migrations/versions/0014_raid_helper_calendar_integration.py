"""add Raid-Helper calendar integration

Revision ID: 0014_raid_helper_calendar
Revises: 0013_legal_notice
Create Date: 2026-07-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0014_raid_helper_calendar"
down_revision: str = "0013_legal_notice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("fleet_events") as batch:
        batch.add_column(sa.Column("raid_helper_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.create_index("ix_fleet_events_raid_helper_enabled", ["raid_helper_enabled"])

    op.create_table(
        "raid_helper_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("server_id", sa.String(32), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("api_base_url", sa.String(200), nullable=False, server_default="https://raid-helper.xyz/api/v4"),
        sa.Column("authorization_mode", sa.String(24), nullable=False, server_default="authorization"),
        sa.Column("timezone", sa.String(80), nullable=False, server_default="Europe/Berlin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_username", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "authorization_mode IN ('authorization', 'bearer', 'x-api-key')",
            name="ck_raid_helper_profile_authorization_mode",
        ),
        sa.UniqueConstraint("name", name="uq_raid_helper_profiles_name"),
    )
    op.create_index("ix_raid_helper_profiles_server_id", "raid_helper_profiles", ["server_id"])
    op.create_index("ix_raid_helper_profiles_is_active", "raid_helper_profiles", ["is_active"])

    op.create_table(
        "raid_helper_destinations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("raid_helper_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("channel_id", sa.String(32), nullable=False),
        sa.Column("scope_type", sa.String(16), nullable=False),
        sa.Column("squad_id", sa.Integer(), sa.ForeignKey("squads.id", ondelete="CASCADE"), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("scope_type IN ('fleet', 'squad')", name="ck_raid_helper_destination_scope"),
        sa.CheckConstraint(
            "(scope_type = 'fleet' AND squad_id IS NULL) OR (scope_type = 'squad' AND squad_id IS NOT NULL)",
            name="ck_raid_helper_destination_scope_target",
        ),
    )
    op.create_index("ix_raid_helper_destinations_profile_id", "raid_helper_destinations", ["profile_id"])
    op.create_index("ix_raid_helper_destinations_squad_id", "raid_helper_destinations", ["squad_id"])
    op.create_index("ix_raid_helper_destinations_is_active", "raid_helper_destinations", ["is_active"])
    op.create_index("ix_raid_helper_destinations_scope", "raid_helper_destinations", ["scope_type", "squad_id", "is_active"])
    op.create_index(
        "uq_raid_helper_destinations_fleet_channel",
        "raid_helper_destinations",
        ["profile_id", "channel_id"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'fleet'"),
        sqlite_where=sa.text("scope_type = 'fleet'"),
    )
    op.create_index(
        "uq_raid_helper_destinations_squad_channel",
        "raid_helper_destinations",
        ["profile_id", "channel_id", "squad_id"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'squad'"),
        sqlite_where=sa.text("scope_type = 'squad'"),
    )

    op.create_table(
        "raid_helper_destination_categories",
        sa.Column("destination_id", sa.Integer(), sa.ForeignKey("raid_helper_destinations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category", sa.String(80), primary_key=True),
    )

    op.create_table(
        "raid_helper_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("raid_helper_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("raid_template_id", sa.String(80), nullable=False, server_default="Standard"),
        sa.Column("scope_type", sa.String(16), nullable=False, server_default="both"),
        sa.Column("title_template", sa.String(300), nullable=False, server_default="{{event.title}}"),
        sa.Column("description_template", sa.Text(), nullable=False, server_default="{{event.description}}"),
        sa.Column("announcement_template", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload_template_json", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("scope_type IN ('both', 'fleet', 'squad')", name="ck_raid_helper_template_scope"),
        sa.UniqueConstraint("profile_id", "name", name="uq_raid_helper_template_name"),
    )
    op.create_index("ix_raid_helper_templates_profile_id", "raid_helper_templates", ["profile_id"])
    op.create_index("ix_raid_helper_templates_is_active", "raid_helper_templates", ["is_active"])

    op.create_table(
        "raid_helper_template_categories",
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("raid_helper_templates.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category", sa.String(80), primary_key=True),
    )

    op.create_table(
        "raid_helper_event_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("fleet_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_id", sa.Integer(), sa.ForeignKey("raid_helper_destinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("raid_helper_templates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("external_event_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("last_operation", sa.String(16), nullable=False, server_default="create"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("event_id", "destination_id", name="uq_raid_helper_event_destination"),
    )
    for name, columns in (
        ("ix_raid_helper_event_links_event_id", ["event_id"]),
        ("ix_raid_helper_event_links_destination_id", ["destination_id"]),
        ("ix_raid_helper_event_links_template_id", ["template_id"]),
        ("ix_raid_helper_event_links_external_event_id", ["external_event_id"]),
        ("ix_raid_helper_event_links_status_updated", ["status", "updated_at"]),
    ):
        op.create_index(name, "raid_helper_event_links", columns)


def downgrade() -> None:
    op.drop_table("raid_helper_event_links")
    op.drop_table("raid_helper_template_categories")
    op.drop_table("raid_helper_templates")
    op.drop_table("raid_helper_destination_categories")
    op.drop_table("raid_helper_destinations")
    op.drop_table("raid_helper_profiles")
    with op.batch_alter_table("fleet_events") as batch:
        batch.drop_index("ix_fleet_events_raid_helper_enabled")
        batch.drop_column("raid_helper_enabled")
