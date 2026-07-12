"""align ship upgrade slot validation with the six-slot Build Designer

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE ships SET upgrade_slots = 6 WHERE upgrade_slots > 6"))
    with op.batch_alter_table("ships") as batch:
        batch.drop_constraint("ck_ships_upgrade_slots", type_="check")
        batch.create_check_constraint(
            "ck_ships_upgrade_slots",
            "upgrade_slots >= 0 and upgrade_slots <= 6",
        )


def downgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.drop_constraint("ck_ships_upgrade_slots", type_="check")
        batch.create_check_constraint("ck_ships_upgrade_slots", "upgrade_slots >= 0")
