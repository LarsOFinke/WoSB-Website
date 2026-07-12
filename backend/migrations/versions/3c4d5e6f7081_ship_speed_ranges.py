"""Add base and cruise-maximum ship speed endpoints.

Revision ID: 3c4d5e6f7081
Revises: 2b3c4d5e6f70
"""

from alembic import op
import sqlalchemy as sa

revision = "3c4d5e6f7081"
down_revision = "2b3c4d5e6f70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.add_column(sa.Column("speed_min_knots", sa.Float(), nullable=True))
    op.execute("UPDATE ships SET speed_min_knots = speed_knots WHERE speed_min_knots IS NULL")
    with op.batch_alter_table("ships") as batch:
        batch.alter_column("speed_min_knots", existing_type=sa.Float(), nullable=False)
        batch.create_check_constraint("ck_ships_speed_min_knots", "speed_min_knots >= 0")
        batch.create_check_constraint("ck_ships_speed_range", "speed_knots >= speed_min_knots")


def downgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.drop_constraint("ck_ships_speed_range", type_="check")
        batch.drop_constraint("ck_ships_speed_min_knots", type_="check")
        batch.drop_column("speed_min_knots")
