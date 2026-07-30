"""normalize upgrade add-on effects and rate weapon defaults

Revision ID: 0008_normalized_build_rules
Revises: 0007_build_votes_and_roles
Create Date: 2026-07-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0008_normalized_build_rules"
down_revision: str = "0007_build_votes_and_roles"
branch_labels = None
depends_on = None


FEATURE_CODE = "research_upgrade_slot"
FEATURE_EFFECTS = {
    "hull_hp_pct": -5.0,
    "turn_rate_pct": -5.0,
    "hold_capacity_pct": -5.0,
}
WEAPON_CLASSES = {
    "light": ("Light", 10),
    "medium": ("Medium", 20),
    "heavy": ("Heavy", 30),
}
RATE_CLASSES = {
    1: "heavy",
    2: "heavy",
    3: "medium",
    4: "medium",
    5: "light",
    6: "light",
    7: "light",
}


def upgrade() -> None:
    op.create_table(
        "build_features",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("upgrade_slots_granted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint(
            "upgrade_slots_granted >= 0 and upgrade_slots_granted <= 8",
            name="ck_build_features_upgrade_slots_granted",
        ),
    )
    op.create_index("ix_build_features_code", "build_features", ["code"], unique=True)

    op.create_table(
        "build_feature_effects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("feature_id", sa.Integer(), nullable=False),
        sa.Column("effect_key", sa.String(length=80), nullable=False),
        sa.Column("effect_value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["feature_id"], ["build_features.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "feature_id", "effect_key", name="uq_build_feature_effect_key"
        ),
    )
    op.create_index(
        "ix_build_feature_effects_feature_id",
        "build_feature_effects",
        ["feature_id"],
    )
    op.create_index(
        "ix_build_feature_effects_effect_key",
        "build_feature_effects",
        ["effect_key"],
    )

    op.create_table(
        "ship_rate_weapon_class_rules",
        sa.Column("rate", sa.Integer(), primary_key=True),
        sa.Column("weapon_class_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "rate >= 1 and rate <= 7", name="ck_ship_rate_weapon_class_rate"
        ),
        sa.ForeignKeyConstraint(
            ["weapon_class_id"], ["weapon_classes.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_ship_rate_weapon_class_rules_weapon_class_id",
        "ship_rate_weapon_class_rules",
        ["weapon_class_id"],
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO build_features "
            "(code, label, upgrade_slots_granted, is_active) "
            "VALUES (:code, :label, :slots, :active)"
        ),
        {
            "code": FEATURE_CODE,
            "label": "Upgrade add-on slot",
            "slots": 1,
            "active": True,
        },
    )
    feature_id = connection.execute(
        sa.text("SELECT id FROM build_features WHERE code = :code"),
        {"code": FEATURE_CODE},
    ).scalar_one()
    for effect_key, effect_value in FEATURE_EFFECTS.items():
        connection.execute(
            sa.text(
                "INSERT INTO build_feature_effects "
                "(feature_id, effect_key, effect_value) "
                "VALUES (:feature_id, :effect_key, :effect_value)"
            ),
            {
                "feature_id": feature_id,
                "effect_key": effect_key,
                "effect_value": effect_value,
            },
        )

    # Alembic migrations run before the application seed process on fresh
    # installations. Ensure the referenced normalized taxonomy exists without
    # overwriting labels or ranks on an existing installation.
    for class_code, (label, rank) in WEAPON_CLASSES.items():
        weapon_class_id = connection.execute(
            sa.text("SELECT id FROM weapon_classes WHERE code = :code"),
            {"code": class_code},
        ).scalar_one_or_none()
        if weapon_class_id is None:
            connection.execute(
                sa.text(
                    "INSERT INTO weapon_classes (code, label, rank) "
                    "VALUES (:code, :label, :rank)"
                ),
                {"code": class_code, "label": label, "rank": rank},
            )

    for rate, class_code in RATE_CLASSES.items():
        weapon_class_id = connection.execute(
            sa.text("SELECT id FROM weapon_classes WHERE code = :code"),
            {"code": class_code},
        ).scalar_one()
        connection.execute(
            sa.text(
                "INSERT INTO ship_rate_weapon_class_rules (rate, weapon_class_id) "
                "VALUES (:rate, :weapon_class_id)"
            ),
            {"rate": rate, "weapon_class_id": weapon_class_id},
        )

    # Repair legacy/custom ships that were stored before rate-driven defaults
    # existed. Only empty regular weapon mounts are filled. Explicit classes,
    # mortar mounts, special-weapon mounts, and zero-capacity placeholders are
    # intentionally left untouched.
    regular_slot_codes = (
        "weapon_front",
        "weapon_rear",
        "weapon_port",
        "weapon_starboard",
    )
    connection.execute(
        sa.text(
            "UPDATE ship_weapon_mounts "
            "SET max_weapon_class_id = ("
            "  SELECT rules.weapon_class_id "
            "  FROM ships "
            "  JOIN ship_rate_weapon_class_rules AS rules "
            "    ON rules.rate = ships.rate "
            "  WHERE ships.id = ship_weapon_mounts.ship_id"
            ") "
            "WHERE max_weapon_class_id IS NULL "
            "  AND capacity > 0 "
            "  AND slot_type_id IN ("
            "    SELECT id FROM weapon_slot_types "
            "    WHERE code IN (:front, :rear, :port, :starboard)"
            "  ) "
            "  AND EXISTS ("
            "    SELECT 1 "
            "    FROM ships "
            "    JOIN ship_rate_weapon_class_rules AS rules "
            "      ON rules.rate = ships.rate "
            "    WHERE ships.id = ship_weapon_mounts.ship_id"
            "  )"
        ),
        {
            "front": regular_slot_codes[0],
            "rear": regular_slot_codes[1],
            "port": regular_slot_codes[2],
            "starboard": regular_slot_codes[3],
        },
    )

    with op.batch_alter_table("builds") as batch_op:
        batch_op.add_column(
            sa.Column("research_upgrade_feature_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_builds_research_upgrade_feature_id",
            "build_features",
            ["research_upgrade_feature_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_builds_research_upgrade_feature_id",
            ["research_upgrade_feature_id"],
        )

    connection.execute(
        sa.text(
            "UPDATE builds SET research_upgrade_feature_id = :feature_id "
            "WHERE research_upgrade_slot_unlocked = :enabled"
        ),
        {"feature_id": feature_id, "enabled": True},
    )

    with op.batch_alter_table("builds") as batch_op:
        batch_op.drop_column("research_upgrade_slot_unlocked")


def downgrade() -> None:
    connection = op.get_bind()
    with op.batch_alter_table("builds") as batch_op:
        batch_op.add_column(
            sa.Column(
                "research_upgrade_slot_unlocked",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    feature_id = connection.execute(
        sa.text("SELECT id FROM build_features WHERE code = :code"),
        {"code": FEATURE_CODE},
    ).scalar_one_or_none()
    if feature_id is not None:
        connection.execute(
            sa.text(
                "UPDATE builds SET research_upgrade_slot_unlocked = :enabled "
                "WHERE research_upgrade_feature_id = :feature_id"
            ),
            {"enabled": True, "feature_id": feature_id},
        )

    with op.batch_alter_table("builds") as batch_op:
        batch_op.drop_index("ix_builds_research_upgrade_feature_id")
        batch_op.drop_constraint(
            "fk_builds_research_upgrade_feature_id", type_="foreignkey"
        )
        batch_op.drop_column("research_upgrade_feature_id")

    op.drop_index(
        "ix_ship_rate_weapon_class_rules_weapon_class_id",
        table_name="ship_rate_weapon_class_rules",
    )
    op.drop_table("ship_rate_weapon_class_rules")
    op.drop_index(
        "ix_build_feature_effects_effect_key", table_name="build_feature_effects"
    )
    op.drop_index(
        "ix_build_feature_effects_feature_id", table_name="build_feature_effects"
    )
    op.drop_table("build_feature_effects")
    op.drop_index("ix_build_features_code", table_name="build_features")
    op.drop_table("build_features")
