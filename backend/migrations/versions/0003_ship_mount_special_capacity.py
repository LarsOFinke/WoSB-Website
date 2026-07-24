"""add positional special-weapon capacity to ship mounts

Revision ID: 0003_mount_special_capacity
Revises: 0002_build_discovery
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_mount_special_capacity"
down_revision: Union[str, Sequence[str], None] = "0002_build_discovery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("ship_weapon_mounts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "special_weapon_capacity",
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.create_check_constraint(
            "ck_ship_weapon_mount_special_capacity",
            "special_weapon_capacity >= 0 and special_weapon_capacity <= capacity",
        )


def downgrade() -> None:
    with op.batch_alter_table("ship_weapon_mounts", schema=None) as batch_op:
        batch_op.drop_constraint(
            "ck_ship_weapon_mount_special_capacity",
            type_="check",
        )
        batch_op.drop_column("special_weapon_capacity")
