"""extend ship and Build Designer upgrade capacity to seven slots

Revision ID: 1a2b3c4d5e6f
Revises: 0f1e2d3c4b5a
"""

from alembic import op

revision = "1a2b3c4d5e6f"
down_revision = "0f1e2d3c4b5a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.drop_constraint("ck_ships_upgrade_slots", type_="check")
        batch.create_check_constraint(
            "ck_ships_upgrade_slots",
            "upgrade_slots >= 0 and upgrade_slots <= 7",
        )


def downgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.drop_constraint("ck_ships_upgrade_slots", type_="check")
        batch.create_check_constraint(
            "ck_ships_upgrade_slots",
            "upgrade_slots >= 0 and upgrade_slots <= 6",
        )
