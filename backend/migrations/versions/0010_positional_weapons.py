"""model normal bow/stern weapons by slot compatibility

Revision ID: 0010_positional_weapons
Revises: 0009_weapon_allowances
Create Date: 2026-07-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0010_positional_weapons"
down_revision: str = "0009_weapon_allowances"
branch_labels = None
depends_on = None


BOW_STERN_CLASSES = {
    "light": (
        ("twin-6-pdr", "Twin 6-pdr"),
        ("triple-10-pdr", "Triple 10-pdr"),
    ),
    "medium": (
        ("basilisk", "Basilisk"),
        ("onager", "Onager"),
        ("twin-14-pdr", "Twin 14-pdr"),
        ("triple-16-pdr", "Triple 16-pdr"),
    ),
    "heavy": (
        ("gilgamesh", "Gilgamesh"),
        ("mjolnir", "Mjolnir"),
        ("poseidon", "Poseidon"),
        ("twin-20-pdr", "Twin 20-pdr"),
        ("zeus", "Zeus"),
    ),
}

LEGACY_ALLOWANCES = (
    ("azov", "Azov", "weapon_front", "zeus", "Zeus"),
    ("azov", "Azov", "weapon_rear", "zeus", "Zeus"),
    ("deadfish", "Deadfish", "weapon_front", "zeus", "Zeus"),
    ("deadfish", "Deadfish", "weapon_rear", "zeus", "Zeus"),
    ("eagle", "Eagle", "weapon_rear", "basilisk", "Basilisk"),
    ("eagle", "Eagle", "weapon_rear", "poseidon", "Poseidon"),
)


def upgrade() -> None:
    connection = op.get_bind()

    # Bow/stern assemblies are a normal positional weapon family. Their
    # compatibility is defined by normalized option-to-slot links, not by the
    # Light/Medium/Heavy broadside ceiling.
    connection.execute(
        sa.text(
            "UPDATE build_item_options "
            "SET weapon_class_id = NULL "
            "WHERE option_kind = 'bow_stern'"
        )
    )

    # The ship-specific table from 0009 represented a mistaken compatibility
    # model. Once positional weapons are slot-driven, those rows are redundant.
    op.drop_index(
        "ix_ship_weapon_option_allowances_build_item_option_id",
        table_name="ship_weapon_option_allowances",
    )
    op.drop_index(
        "ix_ship_weapon_option_allowances_ship_weapon_mount_id",
        table_name="ship_weapon_option_allowances",
    )
    op.drop_table("ship_weapon_option_allowances")


def downgrade() -> None:
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
    restore_class = sa.text(
        "UPDATE build_item_options "
        "SET weapon_class_id = ("
        "  SELECT id FROM weapon_classes WHERE code = :class_code"
        ") "
        "WHERE option_kind = 'bow_stern' "
        "  AND ("
        "    seed_key = :weapon_seed_key "
        "    OR ("
        "      name = :weapon_name "
        "      AND NOT EXISTS ("
        "        SELECT 1 FROM build_item_options AS seeded_option "
        "        WHERE seeded_option.seed_key = :weapon_seed_key"
        "      )"
        "    )"
        "  )"
    )
    for class_code, weapons in BOW_STERN_CLASSES.items():
        for weapon_seed_id, weapon_name in weapons:
            connection.execute(
                restore_class,
                {
                    "class_code": class_code,
                    "weapon_seed_key": f"build-option:weapon:{weapon_seed_id}",
                    "weapon_name": weapon_name,
                },
            )

    insert_allowance = sa.text(
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
        "  AND category.key = 'weapon'"
    )
    for ship_seed_id, ship_name, slot_type, weapon_seed_id, weapon_name in LEGACY_ALLOWANCES:
        connection.execute(
            insert_allowance,
            {
                "ship_seed_key": f"ship:{ship_seed_id}",
                "ship_name": ship_name,
                "slot_type": slot_type,
                "weapon_seed_key": f"build-option:weapon:{weapon_seed_id}",
                "weapon_name": weapon_name,
            },
        )
