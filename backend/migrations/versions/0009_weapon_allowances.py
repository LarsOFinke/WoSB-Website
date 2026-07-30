"""normalize audited per-mount weapon compatibility exceptions

Revision ID: 0009_weapon_allowances
Revises: 0008_normalized_build_rules
Create Date: 2026-07-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0009_weapon_allowances"
down_revision: str = "0008_normalized_build_rules"
branch_labels = None
depends_on = None


ALLOWANCES = (
    ("azov", "Azov", "weapon_front", "zeus", "Zeus"),
    ("azov", "Azov", "weapon_rear", "zeus", "Zeus"),
    ("deadfish", "Deadfish", "weapon_front", "zeus", "Zeus"),
    ("deadfish", "Deadfish", "weapon_rear", "zeus", "Zeus"),
    ("eagle", "Eagle", "weapon_rear", "basilisk", "Basilisk"),
    ("eagle", "Eagle", "weapon_rear", "poseidon", "Poseidon"),
)


def upgrade() -> None:
    op.create_table(
        "ship_weapon_option_allowances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ship_weapon_mount_id", sa.Integer(), nullable=False),
        sa.Column("build_item_option_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ship_weapon_mount_id"],
            ["ship_weapon_mounts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["build_item_option_id"],
            ["build_item_options.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "ship_weapon_mount_id",
            "build_item_option_id",
            name="uq_ship_weapon_option_allowance",
        ),
    )
    op.create_index(
        "ix_ship_weapon_option_allowances_ship_weapon_mount_id",
        "ship_weapon_option_allowances",
        ["ship_weapon_mount_id"],
    )
    op.create_index(
        "ix_ship_weapon_option_allowances_build_item_option_id",
        "ship_weapon_option_allowances",
        ["build_item_option_id"],
    )

    connection = op.get_bind()
    insert = sa.text(
        "INSERT INTO ship_weapon_option_allowances "
        "(ship_weapon_mount_id, build_item_option_id) "
        "SELECT mount.id, option_row.id "
        "FROM ships AS ship "
        "JOIN ship_weapon_mounts AS mount ON mount.ship_id = ship.id "
        "JOIN weapon_slot_types AS slot_type ON slot_type.id = mount.slot_type_id "
        "JOIN build_item_options AS option_row ON ("
        "  option_row.seed_key = :weapon_seed_key "
        "  OR ("
        "    option_row.name = :weapon_name "
        "    AND NOT EXISTS ("
        "      SELECT 1 FROM build_item_options AS seeded_option "
        "      WHERE seeded_option.seed_key = :weapon_seed_key"
        "    )"
        "  )"
        ") "
        "JOIN build_item_categories AS category ON category.id = option_row.category_id "
        "WHERE ("
        "  ship.seed_key = :ship_seed_key "
        "  OR ("
        "    ship.name = :ship_name "
        "    AND NOT EXISTS ("
        "      SELECT 1 FROM ships AS seeded_ship "
        "      WHERE seeded_ship.seed_key = :ship_seed_key"
        "    )"
        "  )"
        ") "
        "  AND slot_type.code = :slot_type "
        "  AND category.key = 'weapon' "
        "  AND NOT EXISTS ("
        "    SELECT 1 FROM ship_weapon_option_allowances AS existing "
        "    WHERE existing.ship_weapon_mount_id = mount.id "
        "      AND existing.build_item_option_id = option_row.id"
        "  )"
    )
    for ship_seed_id, ship_name, slot_type, weapon_seed_id, weapon_name in ALLOWANCES:
        connection.execute(
            insert,
            {
                "ship_seed_key": f"ship:{ship_seed_id}",
                "ship_name": ship_name,
                "slot_type": slot_type,
                "weapon_seed_key": f"build-option:weapon:{weapon_seed_id}",
                "weapon_name": weapon_name,
            },
        )


def downgrade() -> None:
    op.drop_index(
        "ix_ship_weapon_option_allowances_build_item_option_id",
        table_name="ship_weapon_option_allowances",
    )
    op.drop_index(
        "ix_ship_weapon_option_allowances_ship_weapon_mount_id",
        table_name="ship_weapon_option_allowances",
    )
    op.drop_table("ship_weapon_option_allowances")
