"""Encrypt-ready webhook storage and remove obsolete avatar overrides.

Revision ID: 0005_webhook_security
Revises: 0004_mortar_modification
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_webhook_security"
down_revision: str | None = "0004_mortar_modification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("outbound_webhooks") as batch_op:
        batch_op.alter_column(
            "endpoint_url",
            existing_type=sa.String(length=1000),
            type_=sa.Text(),
            existing_nullable=False,
        )
        batch_op.drop_column("discord_avatar_url")


def downgrade() -> None:
    with op.batch_alter_table("outbound_webhooks") as batch_op:
        batch_op.add_column(
            sa.Column("discord_avatar_url", sa.String(length=1000), nullable=True)
        )
        batch_op.alter_column(
            "endpoint_url",
            existing_type=sa.Text(),
            type_=sa.String(length=1000),
            existing_nullable=False,
        )
