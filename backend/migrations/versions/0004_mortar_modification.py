"""add permanent ship mortar modifications to builds

Revision ID: 0004_mortar_modification
Revises: 0003_mount_special_capacity
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_mortar_modification"
down_revision: Union[str, Sequence[str], None] = "0003_mount_special_capacity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ship_mortar_modifications",
        sa.Column("ship_id", sa.Integer(), nullable=False),
        sa.Column("mortar_capacity", sa.Integer(), nullable=False),
        sa.Column("max_caliber_inches", sa.Float(), nullable=False),
        sa.Column("broadside_capacity_delta", sa.Integer(), nullable=False),
        sa.Column("durability_delta", sa.Integer(), nullable=False),
        sa.Column("speed_pct", sa.Float(), nullable=False),
        sa.Column("maneuverability_delta", sa.Float(), nullable=False),
        sa.Column("hold_capacity_pct", sa.Float(), nullable=False),
        sa.Column("crew_capacity_delta", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=500), nullable=False),
        sa.CheckConstraint(
            "broadside_capacity_delta <= 0",
            name="ck_ship_mortar_mod_broadside_delta",
        ),
        sa.CheckConstraint(
            "crew_capacity_delta <= 0",
            name="ck_ship_mortar_mod_crew_delta",
        ),
        sa.CheckConstraint(
            "durability_delta <= 0",
            name="ck_ship_mortar_mod_durability_delta",
        ),
        sa.CheckConstraint(
            "max_caliber_inches > 0",
            name="ck_ship_mortar_mod_max_caliber",
        ),
        sa.CheckConstraint(
            "mortar_capacity > 0",
            name="ck_ship_mortar_mod_capacity",
        ),
        sa.CheckConstraint(
            "speed_pct > -100 and hold_capacity_pct > -100",
            name="ck_ship_mortar_mod_percentage_range",
        ),
        sa.ForeignKeyConstraint(
            ["ship_id"],
            ["ships.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("ship_id"),
    )
    with op.batch_alter_table("builds", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "mortar_modification_installed",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("builds", schema=None) as batch_op:
        batch_op.drop_column("mortar_modification_installed")
    op.drop_table("ship_mortar_modifications")
