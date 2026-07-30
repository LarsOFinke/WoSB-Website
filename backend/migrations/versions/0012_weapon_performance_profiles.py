"""add normalized weapon performance profiles

Revision ID: 0012_weapon_performance_profiles
Revises: 0011_positional_weapon_classes
Create Date: 2026-07-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0012_weapon_performance_profiles"
down_revision: str = "0011_positional_weapon_classes"
branch_labels = None
depends_on = None


# Audited from the project-owner cannon comparison supplied on 2026-07-30.
# Bow/stern profiles are intentionally not invented; they can be maintained in
# Staff Master Data once verified values are available.
WEAPON_PROFILES = (
    ("6-pdr-rusty-cannon", "6-pdr Rusty Cannon", 13.0, 10.5),
    ("8-pdr-cannon", "8-pdr Cannon", 14.0, 9.0),
    ("6-pdr-culverin", "6-pdr Culverin", 14.0, 15.5),
    ("8-pdr-culverin", "8-pdr Culverin", 15.0, 13.0),
    ("12-pdr-carronade", "12-pdr Carronade", 20.0, 22.0),
    ("16-pdr-carronade", "16-pdr Carronade", 21.5, 19.5),
    ("16-pdr-cannon", "16-pdr Cannon", 14.0, 12.0),
    ("18-pdr-cannon", "18-pdr Cannon", 15.0, 10.5),
    ("20-pdr-admiral", "20-pdr Admiral", 17.0, 13.5),
    ("16-pdr-culverin", "16-pdr Culverin", 15.0, 17.5),
    ("18-pdr-long-cannon", "18-pdr Long Cannon", 16.0, 15.0),
    ("22-pdr-scorcher", "22-pdr Scorcher", 19.0, 26.0),
    ("24-pdr-carronade", "24-pdr Carronade", 21.5, 25.5),
    ("28-pdr-carronade", "28-pdr Carronade", 23.0, 22.5),
    ("32-pdr-stormbringer", "32-pdr Stormbringer", 25.5, 27.5),
    ("32-pdr-cannon", "32-pdr Cannon", 17.5, 12.0),
    ("36-pdr-inrog", "36-pdr Inrog", 20.0, 16.0),
    ("32-pdr-long-cannon", "32-pdr Long Cannon", 18.5, 17.5),
    ("38-pdr-jericho", "38-pdr Jericho", 22.0, 30.5),
    ("42-pdr-carronade", "42-pdr Carronade", 27.0, 26.0),
    ("48-pdr-colossus", "48-pdr Colossus", 30.0, 32.0),
)


def upgrade() -> None:
    op.create_table(
        "weapon_performance_profiles",
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("base_damage", sa.Float(), nullable=False),
        sa.Column("reload_seconds", sa.Float(), nullable=False),
        sa.CheckConstraint("base_damage >= 0", name="ck_weapon_performance_damage"),
        sa.CheckConstraint("reload_seconds > 0", name="ck_weapon_performance_reload"),
        sa.ForeignKeyConstraint(
            ["option_id"], ["build_item_options.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("option_id"),
    )

    connection = op.get_bind()
    option_lookup = sa.text(
        "SELECT id FROM build_item_options "
        "WHERE seed_key = :seed_key "
        "   OR (name = :name AND category_id = ("
        "       SELECT id FROM build_item_categories WHERE key = 'weapon'"
        "   )) "
        "ORDER BY CASE WHEN seed_key = :seed_key THEN 0 ELSE 1 END "
        "LIMIT 1"
    )
    insert_profile = sa.text(
        "INSERT INTO weapon_performance_profiles "
        "(option_id, base_damage, reload_seconds) "
        "VALUES (:option_id, :base_damage, :reload_seconds)"
    )
    for seed_id, name, damage, reload_seconds in WEAPON_PROFILES:
        option_id = connection.execute(
            option_lookup,
            {
                "seed_key": f"build-option:weapon:{seed_id}",
                "name": name,
            },
        ).scalar()
        if option_id is not None:
            connection.execute(
                insert_profile,
                {
                    "option_id": option_id,
                    "base_damage": damage,
                    "reload_seconds": reload_seconds,
                },
            )


def downgrade() -> None:
    op.drop_table("weapon_performance_profiles")
