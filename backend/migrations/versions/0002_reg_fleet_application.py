"""restore optional fleet application during registration

Revision ID: 0002_reg_fleet_application
Revises: 0001_baseline
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_reg_fleet_application"
down_revision: Union[str, Sequence[str], None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("registration_requests") as batch_op:
        batch_op.add_column(
            sa.Column("wants_fleet_membership", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(sa.Column("fleet_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("fleet_application_note", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_registration_requests_fleet_id_fleets",
            "fleets",
            ["fleet_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_registration_requests_fleet_id", ["fleet_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("registration_requests") as batch_op:
        batch_op.drop_index("ix_registration_requests_fleet_id")
        batch_op.drop_constraint("fk_registration_requests_fleet_id_fleets", type_="foreignkey")
        batch_op.drop_column("fleet_application_note")
        batch_op.drop_column("fleet_id")
        batch_op.drop_column("wants_fleet_membership")
