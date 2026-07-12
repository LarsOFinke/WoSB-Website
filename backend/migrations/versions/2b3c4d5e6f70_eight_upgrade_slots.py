"""extend ship and Build Designer upgrade capacity to eight slots

Revision ID: 2b3c4d5e6f70
Revises: 1a2b3c4d5e6f
"""

from alembic import op

revision = "2b3c4d5e6f70"
down_revision = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.drop_constraint("ck_ships_upgrade_slots", type_="check")
        batch.create_check_constraint(
            "ck_ships_upgrade_slots",
            "upgrade_slots >= 0 and upgrade_slots <= 8",
        )


def downgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.drop_constraint("ck_ships_upgrade_slots", type_="check")
        batch.create_check_constraint(
            "ck_ships_upgrade_slots",
            "upgrade_slots >= 0 and upgrade_slots <= 7",
        )
