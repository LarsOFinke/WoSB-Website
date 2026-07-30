"""Add profile defaults and per-event Raid-Helper leader overrides.

Revision ID: 0017_raid_helper_leaders
Revises: 0016_raid_helper_api_host
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0017_raid_helper_leaders"
down_revision: str = "0016_raid_helper_api_host"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("raid_helper_profiles") as batch:
        batch.add_column(sa.Column("default_leader_id", sa.String(length=32), nullable=True))
    with op.batch_alter_table("raid_helper_event_links") as batch:
        batch.add_column(sa.Column("leader_id_override", sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("raid_helper_event_links") as batch:
        batch.drop_column("leader_id_override")
    with op.batch_alter_table("raid_helper_profiles") as batch:
        batch.drop_column("default_leader_id")
