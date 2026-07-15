"""generalize webhooks and enable managed fleet roles

Revision ID: 0003_webhooks_fleet_roles
Revises: 0002_reg_fleet_application
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_webhooks_fleet_roles"
down_revision: Union[str, Sequence[str], None] = "0002_reg_fleet_application"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("fleet_roles") as batch_op:
        batch_op.add_column(
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        batch_op.create_index("ix_fleet_roles_is_system", ["is_system"], unique=False)
        batch_op.create_index("ix_fleet_roles_is_active", ["is_active"], unique=False)

    op.execute(
        sa.text(
            "UPDATE fleet_roles SET is_system = true "
            "WHERE code IN ('member', 'fleet_lieutenant', 'fleet_admiral')"
        )
    )

    with op.batch_alter_table("outbound_webhooks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "delivery_mode",
                sa.String(length=24),
                nullable=False,
                server_default="signed_json",
            )
        )
        batch_op.add_column(
            sa.Column(
                "scope_type", sa.String(length=24), nullable=False, server_default="global"
            )
        )
        batch_op.add_column(sa.Column("scope_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("discord_username", sa.String(length=80), nullable=True))
        batch_op.add_column(
            sa.Column("discord_avatar_url", sa.String(length=1000), nullable=True)
        )
        batch_op.create_index(
            "ix_outbound_webhooks_delivery_mode", ["delivery_mode"], unique=False
        )
        batch_op.create_index("ix_outbound_webhooks_scope_type", ["scope_type"], unique=False)
        batch_op.create_index("ix_outbound_webhooks_scope_id", ["scope_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("outbound_webhooks") as batch_op:
        batch_op.drop_index("ix_outbound_webhooks_scope_id")
        batch_op.drop_index("ix_outbound_webhooks_scope_type")
        batch_op.drop_index("ix_outbound_webhooks_delivery_mode")
        batch_op.drop_column("discord_avatar_url")
        batch_op.drop_column("discord_username")
        batch_op.drop_column("scope_id")
        batch_op.drop_column("scope_type")
        batch_op.drop_column("delivery_mode")

    with op.batch_alter_table("fleet_roles") as batch_op:
        batch_op.drop_index("ix_fleet_roles_is_active")
        batch_op.drop_index("ix_fleet_roles_is_system")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("is_active")
        batch_op.drop_column("is_system")
