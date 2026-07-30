"""Make Raid-Helper template IDs optional and remove the legacy Standard sentinel.

Revision ID: 0019_raid_helper_template_id
Revises: 0018_raid_helper_raw_auth
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0019_raid_helper_template_id"
down_revision: str = "0018_raid_helper_raw_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Earlier releases inserted the literal ``Standard`` even though the
    # create-event API treats templateId as optional. Existing records using
    # that application default should therefore fall back to the server's
    # normal/default Raid-Helper template instead of requesting a template ID.
    op.execute(
        sa.text(
            """
            UPDATE raid_helper_templates
            SET raid_template_id = ''
            WHERE lower(trim(raid_template_id)) = 'standard'
            """
        )
    )
    with op.batch_alter_table("raid_helper_templates") as batch:
        batch.alter_column(
            "raid_template_id",
            existing_type=sa.String(length=80),
            nullable=False,
            server_default="",
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE raid_helper_templates
            SET raid_template_id = 'Standard'
            WHERE trim(raid_template_id) = ''
            """
        )
    )
    with op.batch_alter_table("raid_helper_templates") as batch:
        batch.alter_column(
            "raid_template_id",
            existing_type=sa.String(length=80),
            nullable=False,
            server_default="Standard",
        )
