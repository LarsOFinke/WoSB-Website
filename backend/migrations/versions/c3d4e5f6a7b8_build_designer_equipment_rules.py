"""add persisted research upgrade slot toggle

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("builds") as batch:
        batch.add_column(
            sa.Column(
                "research_upgrade_slot_unlocked",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("builds") as batch:
        batch.drop_column("research_upgrade_slot_unlocked")
