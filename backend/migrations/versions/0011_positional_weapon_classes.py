"""apply size classes to standard bow/stern weapons

Revision ID: 0011_positional_weapon_classes
Revises: 0010_positional_weapons
Create Date: 2026-07-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0011_positional_weapon_classes"
down_revision: str = "0010_positional_weapons"
branch_labels = None
depends_on = None


# Bow/stern assemblies use the same normalized Light/Medium/Heavy ceiling as
# broadside cannons. Named weapons are classified by their audited in-game
# compatibility rather than by per-ship exception rows.
BOW_STERN_CLASSES = {
    "light": (
        ("twin-6-pdr", "Twin 6-pdr"),
        ("triple-10-pdr", "Triple 10-pdr"),
        ("basilisk", "Basilisk"),
        ("poseidon", "Poseidon"),
    ),
    "medium": (
        ("onager", "Onager"),
        ("twin-14-pdr", "Twin 14-pdr"),
        ("triple-16-pdr", "Triple 16-pdr"),
        ("zeus", "Zeus"),
    ),
    "heavy": (
        ("gilgamesh", "Gilgamesh"),
        ("mjolnir", "Mjolnir"),
        ("twin-20-pdr", "Twin 20-pdr"),
    ),
}


def upgrade() -> None:
    connection = op.get_bind()
    assign_class = sa.text(
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
                assign_class,
                {
                    "class_code": class_code,
                    "weapon_seed_key": f"build-option:weapon:{weapon_seed_id}",
                    "weapon_name": weapon_name,
                },
            )


def downgrade() -> None:
    # Revision 0010 intentionally modeled positional weapons by slot only.
    # Restore that historical state when downgrading to it.
    op.get_bind().execute(
        sa.text(
            "UPDATE build_item_options "
            "SET weapon_class_id = NULL "
            "WHERE option_kind = 'bow_stern'"
        )
    )
