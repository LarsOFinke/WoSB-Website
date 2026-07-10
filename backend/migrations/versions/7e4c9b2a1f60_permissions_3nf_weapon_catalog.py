"""normalize permissions, registration, fleet preferences, and weapon taxonomy

Revision ID: 7e4c9b2a1f60
Revises: 5d9a3b7c1e20
Create Date: 2026-07-10 21:15:00.000000
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa

revision: str = "7e4c9b2a1f60"
down_revision: Union[str, Sequence[str], None] = "5d9a3b7c1e20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SITE_ROLES = (
    ("user", "User", 10, False, False),
    ("moderator", "Moderator", 50, True, False),
    ("admin", "Administrator", 100, True, True),
)
FLEET_ROLES = (
    ("member", "Fleet Member", 10, False, False, False),
    ("fleet_lieutenant", "Fleet Lieutenant", 60, True, True, True),
    ("fleet_admiral", "Fleet Admiral", 80, True, True, True),
)
SQUAD_ROLES = (
    ("member", "Squad Member", 10, False, False),
    ("officer", "Squad Officer", 50, True, True),
    ("leader", "Squad Leader", 80, True, True),
)
WEAPON_CLASSES = (
    ("light", "Light", 10),
    ("medium", "Medium", 20),
    ("heavy", "Heavy", 30),
)
SLOT_TYPES = (
    ("weapon_front", "Bow weapons", 10),
    ("weapon_rear", "Stern weapons", 20),
    ("weapon_port", "Port broadside", 30),
    ("weapon_starboard", "Starboard broadside", 40),
    ("weapon_mortar", "Mortars", 50),
)
MAX_WEAPON_CLASS_BY_RATE = {
    1: "heavy",
    2: "heavy",
    3: "heavy",
    4: "medium",
    5: "medium",
    6: "light",
    7: "light",
}
LIGHT_WEAPONS = {
    "6-pdr Culverin",
    "6-pdr Rusty Cannon",
    "8-pdr Cannon",
    "8-pdr Culverin",
    "12-pdr Carronade",
    "Alchemical Fire",
    "Barrel Launcher",
    "Twin 6-pdr",
    "Triple 10-pdr",
}
MEDIUM_WEAPONS = {
    "16-pdr Cannon",
    "16-pdr Carronade",
    "16-pdr Culverin",
    "18-pdr Cannon",
    "18-pdr Long Cannon",
    "20-pdr Admiral",
    "22-pdr Scorcher",
    "24-pdr Carronade",
    "28-pdr Carronade",
    "Basilisk",
    "Imperial Bombard",
    "Onager",
    "Twin 14-pdr",
    "Triple 16-pdr",
}
HEAVY_WEAPONS = {
    "32-pdr Cannon",
    "32-pdr Long Cannon",
    "32-pdr Stormbringer",
    "36-pdr Inrog",
    "38-pdr Jericho",
    "42-pdr Carronade",
    "48-pdr Colossus",
    "Gilgamesh",
    "Mjolnir",
    "Poseidon",
    "Twin 20-pdr",
    "Zeus",
}
REGISTRATION_FLEET_COLUMNS = (
    "external_fleet_name",
    "fleet_id",
    "wants_fleet_membership",
    "fleet_application_note",
    "fleet_availability",
    "fleet_preferred_ships",
    "fleet_timezone",
    "fleet_discord_handle",
)


def _parse_layout(layout: str | None, rate: int) -> list[dict[str, object]]:
    text = (layout or "0-0-0").strip().lower().replace(";", " + ")
    regular = re.search(r"(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", text)
    front, side, rear = (map(int, regular.groups()) if regular else (0, 0, 0))
    weapon_class = MAX_WEAPON_CLASS_BY_RATE.get(int(rate), "light")
    rows = [
        {"code": "weapon_front", "capacity": front, "max_weapon_class": weapon_class, "max_caliber_inches": None},
        {"code": "weapon_rear", "capacity": rear, "max_weapon_class": weapon_class, "max_caliber_inches": None},
        {"code": "weapon_port", "capacity": side, "max_weapon_class": weapon_class, "max_caliber_inches": None},
        {"code": "weapon_starboard", "capacity": side, "max_weapon_class": weapon_class, "max_caliber_inches": None},
    ]
    mortar = re.search(r"mortar\s+(\d+(?:\.\d+)?)\s*in\s*x\s*(\d+)", text)
    rows.append(
        {
            "code": "weapon_mortar",
            "capacity": int(mortar.group(2)) if mortar else 0,
            "max_weapon_class": None,
            "max_caliber_inches": float(mortar.group(1)) if mortar else None,
        }
    )
    return rows


def _weapon_class_code(name: str, kind: str | None) -> str | None:
    if kind == "mortar":
        return None
    if name in LIGHT_WEAPONS:
        return "light"
    if name in MEDIUM_WEAPONS:
        return "medium"
    if name in HEAVY_WEAPONS:
        return "heavy"
    match = re.search(r"(\d+(?:\.\d+)?)\s*-?pdr", name, re.IGNORECASE)
    if match:
        pounds = float(match.group(1))
        if pounds <= 12:
            return "light"
        if pounds <= 28:
            return "medium"
        return "heavy"
    return None


def _foreign_key_name(table: str, column: str, *, offline_default: str) -> str | None:
    if context.is_offline_mode():
        return offline_default
    for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys(table):
        if foreign_key.get("constrained_columns") == [column]:
            return foreign_key.get("name")
    return None


def _drop_registration_fleet_columns() -> None:
    fk_name = _foreign_key_name(
        "registration_requests",
        "fleet_id",
        offline_default="registration_requests_fleet_id_fkey",
    )
    if fk_name:
        with op.batch_alter_table("registration_requests") as batch:
            batch.drop_index("ix_registration_requests_fleet_id")
            batch.drop_constraint(fk_name, type_="foreignkey")
            for column in REGISTRATION_FLEET_COLUMNS:
                batch.drop_column(column)
        return

    # SQLite can expose an unnamed foreign key from the original migration.
    with op.batch_alter_table(
        "registration_requests",
        naming_convention={"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"},
    ) as batch:
        batch.drop_index("ix_registration_requests_fleet_id")
        batch.drop_constraint("fk_registration_requests_fleet_id_fleets", type_="foreignkey")
        for column in REGISTRATION_FLEET_COLUMNS:
            batch.drop_column(column)


def _drop_primary_membership_pointer() -> None:
    fk_name = _foreign_key_name(
        "user_profiles",
        "primary_fleet_membership_id",
        offline_default="user_profiles_primary_fleet_membership_id_fkey",
    )
    if fk_name:
        with op.batch_alter_table("user_profiles") as batch:
            batch.drop_index("ix_user_profiles_primary_fleet_membership_id")
            batch.drop_constraint(fk_name, type_="foreignkey")
            batch.drop_column("primary_fleet_membership_id")
        return

    with op.batch_alter_table(
        "user_profiles",
        naming_convention={"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"},
    ) as batch:
        batch.drop_index("ix_user_profiles_primary_fleet_membership_id")
        batch.drop_constraint(
            "fk_user_profiles_primary_fleet_membership_id_fleet_memberships",
            type_="foreignkey",
        )
        batch.drop_column("primary_fleet_membership_id")


def upgrade() -> None:
    bind = op.get_bind()
    offline = context.is_offline_mode()

    op.create_table(
        "site_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("is_staff", sa.Boolean(), nullable=False),
        sa.Column("can_manage_system", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rank >= 0", name="ck_site_roles_rank"),
    )
    op.create_index("ix_site_roles_code", "site_roles", ["code"], unique=True)
    op.create_index("ix_site_roles_rank", "site_roles", ["rank"])
    site_roles = sa.table(
        "site_roles",
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("rank", sa.Integer),
        sa.column("is_staff", sa.Boolean),
        sa.column("can_manage_system", sa.Boolean),
    )
    op.bulk_insert(
        site_roles,
        [dict(zip(("code", "label", "rank", "is_staff", "can_manage_system"), row)) for row in SITE_ROLES],
    )

    op.create_table(
        "fleet_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("is_leadership", sa.Boolean(), nullable=False),
        sa.Column("can_manage_fleet", sa.Boolean(), nullable=False),
        sa.Column("can_manage_members", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rank >= 0", name="ck_fleet_roles_rank"),
    )
    op.create_index("ix_fleet_roles_code", "fleet_roles", ["code"], unique=True)
    op.create_index("ix_fleet_roles_rank", "fleet_roles", ["rank"])
    op.create_index("ix_fleet_roles_is_leadership", "fleet_roles", ["is_leadership"])
    fleet_roles = sa.table(
        "fleet_roles",
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("rank", sa.Integer),
        sa.column("is_leadership", sa.Boolean),
        sa.column("can_manage_fleet", sa.Boolean),
        sa.column("can_manage_members", sa.Boolean),
    )
    op.bulk_insert(
        fleet_roles,
        [
            dict(zip(("code", "label", "rank", "is_leadership", "can_manage_fleet", "can_manage_members"), row))
            for row in FLEET_ROLES
        ],
    )

    op.create_table(
        "squad_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(24), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("can_manage_roster", sa.Boolean(), nullable=False),
        sa.Column("can_manage_events", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rank >= 0", name="ck_squad_roles_rank"),
    )
    op.create_index("ix_squad_roles_code", "squad_roles", ["code"], unique=True)
    op.create_index("ix_squad_roles_rank", "squad_roles", ["rank"])
    squad_roles = sa.table(
        "squad_roles",
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("rank", sa.Integer),
        sa.column("can_manage_roster", sa.Boolean),
        sa.column("can_manage_events", sa.Boolean),
    )
    op.bulk_insert(
        squad_roles,
        [dict(zip(("code", "label", "rank", "can_manage_roster", "can_manage_events"), row)) for row in SQUAD_ROLES],
    )

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("site_role_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_users_site_role_id", "site_roles", ["site_role_id"], ["id"], ondelete="RESTRICT")
        batch.create_index("ix_users_site_role_id", ["site_role_id"])
    if not offline:
        bind.execute(sa.text("UPDATE users SET site_role_id=(SELECT id FROM site_roles WHERE code=users.role)"))
    with op.batch_alter_table("users") as batch:
        batch.alter_column("site_role_id", nullable=False)
        batch.drop_index("ix_users_role")
        batch.drop_constraint("ck_users_role", type_="check")
        batch.drop_column("role")

    with op.batch_alter_table("fleet_memberships") as batch:
        batch.add_column(sa.Column("fleet_role_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_fleet_memberships_fleet_role_id",
            "fleet_roles",
            ["fleet_role_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index("ix_fleet_memberships_fleet_role_id", ["fleet_role_id"])
    if not offline:
        bind.execute(
            sa.text("UPDATE fleet_memberships SET fleet_role_id=(SELECT id FROM fleet_roles WHERE code=fleet_memberships.role)")
        )

    op.create_table(
        "fleet_membership_ship_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fleet_membership_id", sa.Integer(), nullable=False),
        sa.Column("ship_name", sa.String(120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["fleet_membership_id"], ["fleet_memberships.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("fleet_membership_id", "ship_name", name="uq_fleet_membership_ship_preference"),
        sa.CheckConstraint("sort_order >= 0", name="ck_fleet_membership_ship_preferences_sort_order"),
    )
    op.create_index(
        "ix_fleet_membership_ship_preferences_fleet_membership_id",
        "fleet_membership_ship_preferences",
        ["fleet_membership_id"],
    )
    if not offline:
        for membership_id, preferred in bind.execute(
            sa.text("SELECT id, preferred_ships FROM fleet_memberships WHERE preferred_ships IS NOT NULL")
        ):
            seen: set[str] = set()
            order = 10
            for raw in str(preferred).replace(";", ",").split(","):
                name = raw.strip()
                if not name or name.casefold() in seen:
                    continue
                seen.add(name.casefold())
                bind.execute(
                    sa.text(
                        "INSERT INTO fleet_membership_ship_preferences "
                        "(fleet_membership_id, ship_name, sort_order) "
                        "VALUES (:membership_id, :ship_name, :sort_order)"
                    ),
                    {"membership_id": membership_id, "ship_name": name, "sort_order": order},
                )
                order += 10
    with op.batch_alter_table("fleet_memberships") as batch:
        batch.alter_column("fleet_role_id", nullable=False)
        batch.drop_index("ix_fleet_memberships_role")
        batch.drop_constraint("ck_fleet_memberships_role", type_="check")
        batch.drop_column("role")
        batch.drop_column("preferred_ships")

    with op.batch_alter_table("squad_members") as batch:
        batch.add_column(sa.Column("squad_role_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_squad_members_squad_role_id",
            "squad_roles",
            ["squad_role_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index("ix_squad_members_squad_role_id", ["squad_role_id"])
    if not offline:
        bind.execute(
            sa.text("UPDATE squad_members SET squad_role_id=(SELECT id FROM squad_roles WHERE code=squad_members.role)")
        )
    with op.batch_alter_table("squad_members") as batch:
        batch.alter_column("squad_role_id", nullable=False)
        batch.drop_index("ix_squad_members_role")
        batch.drop_constraint("ck_squad_members_role", type_="check")
        batch.drop_column("role")

    _drop_primary_membership_pointer()
    _drop_registration_fleet_columns()

    op.create_table(
        "weapon_classes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(24), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.CheckConstraint("rank >= 0", name="ck_weapon_classes_rank"),
    )
    op.create_index("ix_weapon_classes_code", "weapon_classes", ["code"], unique=True)
    op.create_index("ix_weapon_classes_rank", "weapon_classes", ["rank"])
    weapon_classes = sa.table(
        "weapon_classes",
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("rank", sa.Integer),
    )
    op.bulk_insert(
        weapon_classes,
        [dict(zip(("code", "label", "rank"), row)) for row in WEAPON_CLASSES],
    )

    op.create_table(
        "weapon_slot_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )
    op.create_index("ix_weapon_slot_types_code", "weapon_slot_types", ["code"], unique=True)
    slot_types = sa.table(
        "weapon_slot_types",
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(slot_types, [dict(zip(("code", "label", "sort_order"), row)) for row in SLOT_TYPES])

    class_ids = {} if offline else {
        code: row_id for row_id, code in bind.execute(sa.text("SELECT id, code FROM weapon_classes"))
    }
    slot_ids = {} if offline else {
        code: row_id for row_id, code in bind.execute(sa.text("SELECT id, code FROM weapon_slot_types"))
    }

    op.create_table(
        "ship_weapon_mounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ship_id", sa.Integer(), nullable=False),
        sa.Column("slot_type_id", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("max_weapon_class_id", sa.Integer(), nullable=True),
        sa.Column("max_caliber_inches", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["ship_id"], ["ships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_type_id"], ["weapon_slot_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["max_weapon_class_id"], ["weapon_classes.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("ship_id", "slot_type_id", name="uq_ship_weapon_mount_slot"),
        sa.CheckConstraint("capacity >= 0", name="ck_ship_weapon_mount_capacity"),
        sa.CheckConstraint(
            "max_caliber_inches is null or max_caliber_inches >= 0",
            name="ck_ship_weapon_mount_max_caliber",
        ),
    )
    op.create_index("ix_ship_weapon_mounts_ship_id", "ship_weapon_mounts", ["ship_id"])
    op.create_index("ix_ship_weapon_mounts_slot_type_id", "ship_weapon_mounts", ["slot_type_id"])
    op.create_index("ix_ship_weapon_mounts_max_weapon_class_id", "ship_weapon_mounts", ["max_weapon_class_id"])
    if not offline:
        for ship_id, rate, layout in bind.execute(sa.text("SELECT id, rate, weapon_layout FROM ships")):
            for row in _parse_layout(layout, rate):
                class_code = row["max_weapon_class"]
                bind.execute(
                    sa.text(
                        "INSERT INTO ship_weapon_mounts "
                        "(ship_id, slot_type_id, capacity, max_weapon_class_id, max_caliber_inches) "
                        "VALUES (:ship_id, :slot_type_id, :capacity, :max_weapon_class_id, :max_caliber_inches)"
                    ),
                    {
                        "ship_id": ship_id,
                        "slot_type_id": slot_ids[str(row["code"])],
                        "capacity": row["capacity"],
                        "max_weapon_class_id": class_ids[str(class_code)] if class_code else None,
                        "max_caliber_inches": row["max_caliber_inches"],
                    },
                )

    op.create_table(
        "build_item_option_slot_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("slot_type_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["option_id"], ["build_item_options.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_type_id"], ["weapon_slot_types.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("option_id", "slot_type_id", name="uq_build_item_option_slot_type"),
    )
    op.create_index("ix_build_item_option_slot_types_option_id", "build_item_option_slot_types", ["option_id"])
    op.create_index("ix_build_item_option_slot_types_slot_type_id", "build_item_option_slot_types", ["slot_type_id"])

    with op.batch_alter_table("build_item_options") as batch:
        batch.add_column(sa.Column("weapon_class_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_build_item_options_weapon_class_id",
            "weapon_classes",
            ["weapon_class_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index("ix_build_item_options_weapon_class_id", ["weapon_class_id"])
    if not offline:
        for option_id, name, kind, allowed in bind.execute(
            sa.text("SELECT id, name, option_kind, allowed_slot_types FROM build_item_options")
        ):
            class_code = _weapon_class_code(str(name), kind)
            bind.execute(
                sa.text("UPDATE build_item_options SET weapon_class_id=:class_id WHERE id=:id"),
                {"class_id": class_ids[class_code] if class_code else None, "id": option_id},
            )
            for code in {part.strip() for part in str(allowed or "").split(",") if part.strip()}:
                if code in slot_ids:
                    bind.execute(
                        sa.text(
                            "INSERT INTO build_item_option_slot_types (option_id, slot_type_id) "
                            "VALUES (:option_id, :slot_type_id)"
                        ),
                        {"option_id": option_id, "slot_type_id": slot_ids[code]},
                    )

    with op.batch_alter_table("ships") as batch:
        batch.alter_column("source", existing_type=sa.String(120), type_=sa.String(240), existing_nullable=True)
        batch.drop_column("weapon_layout")
    with op.batch_alter_table("build_item_options") as batch:
        batch.alter_column("source", existing_type=sa.String(120), type_=sa.String(240), existing_nullable=True)
        batch.drop_column("allowed_slot_types")
    with op.batch_alter_table("builds") as batch:
        batch.add_column(sa.Column("is_official_template", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_index("ix_builds_is_official_template", ["is_official_template"])


def downgrade() -> None:
    bind = op.get_bind()
    offline = context.is_offline_mode()

    with op.batch_alter_table("builds") as batch:
        batch.drop_index("ix_builds_is_official_template")
        batch.drop_column("is_official_template")

    with op.batch_alter_table("build_item_options") as batch:
        batch.add_column(sa.Column("allowed_slot_types", sa.String(160), nullable=True))
    if not offline:
        grouped: dict[int, list[str]] = defaultdict(list)
        for option_id, code in bind.execute(
            sa.text(
                "SELECT l.option_id, s.code FROM build_item_option_slot_types l "
                "JOIN weapon_slot_types s ON s.id=l.slot_type_id ORDER BY s.sort_order"
            )
        ):
            grouped[int(option_id)].append(str(code))
        for option_id, codes in grouped.items():
            bind.execute(
                sa.text("UPDATE build_item_options SET allowed_slot_types=:allowed WHERE id=:id"),
                {"allowed": ",".join(codes), "id": option_id},
            )
    with op.batch_alter_table("build_item_options") as batch:
        batch.drop_index("ix_build_item_options_weapon_class_id")
        batch.drop_constraint("fk_build_item_options_weapon_class_id", type_="foreignkey")
        batch.drop_column("weapon_class_id")
        batch.alter_column("source", existing_type=sa.String(240), type_=sa.String(120), existing_nullable=True)

    with op.batch_alter_table("ships") as batch:
        batch.add_column(sa.Column("weapon_layout", sa.String(40), nullable=True))
    if not offline:
        ship_rows: dict[int, dict[str, tuple[int, float | None]]] = defaultdict(dict)
        for ship_id, code, capacity, caliber in bind.execute(
            sa.text(
                "SELECT m.ship_id, s.code, m.capacity, m.max_caliber_inches "
                "FROM ship_weapon_mounts m JOIN weapon_slot_types s ON s.id=m.slot_type_id"
            )
        ):
            ship_rows[int(ship_id)][str(code)] = (int(capacity), float(caliber) if caliber is not None else None)
        for ship_id, mounts in ship_rows.items():
            front = mounts.get("weapon_front", (0, None))[0]
            side = mounts.get("weapon_port", (0, None))[0]
            rear = mounts.get("weapon_rear", (0, None))[0]
            layout = f"{front}-{side}-{rear}"
            mortar_capacity, mortar_caliber = mounts.get("weapon_mortar", (0, None))
            if mortar_capacity > 0 and mortar_caliber is not None:
                caliber_text = int(mortar_caliber) if mortar_caliber.is_integer() else mortar_caliber
                layout += f" + mortar {caliber_text}in x{mortar_capacity}"
            bind.execute(
                sa.text("UPDATE ships SET weapon_layout=:layout WHERE id=:id"),
                {"layout": layout, "id": ship_id},
            )
    with op.batch_alter_table("ships") as batch:
        batch.alter_column("source", existing_type=sa.String(240), type_=sa.String(120), existing_nullable=True)

    op.drop_table("build_item_option_slot_types")
    op.drop_table("ship_weapon_mounts")
    op.drop_table("weapon_slot_types")
    op.drop_table("weapon_classes")

    with op.batch_alter_table("registration_requests") as batch:
        batch.add_column(sa.Column("external_fleet_name", sa.String(120), nullable=True))
        batch.add_column(sa.Column("fleet_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("wants_fleet_membership", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("fleet_application_note", sa.Text(), nullable=True))
        batch.add_column(sa.Column("fleet_availability", sa.String(240), nullable=True))
        batch.add_column(sa.Column("fleet_preferred_ships", sa.String(300), nullable=True))
        batch.add_column(sa.Column("fleet_timezone", sa.String(80), nullable=True))
        batch.add_column(sa.Column("fleet_discord_handle", sa.String(120), nullable=True))
        batch.create_foreign_key(
            "fk_registration_requests_fleet_id",
            "fleets",
            ["fleet_id"],
            ["id"],
        )
        batch.create_index("ix_registration_requests_fleet_id", ["fleet_id"])

    with op.batch_alter_table("user_profiles") as batch:
        batch.add_column(sa.Column("primary_fleet_membership_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_user_profiles_primary_fleet_membership_id",
            "fleet_memberships",
            ["primary_fleet_membership_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_user_profiles_primary_fleet_membership_id", ["primary_fleet_membership_id"])

    with op.batch_alter_table("squad_members") as batch:
        batch.add_column(sa.Column("role", sa.String(24), nullable=True))
    if not offline:
        bind.execute(
            sa.text("UPDATE squad_members SET role=(SELECT code FROM squad_roles WHERE id=squad_members.squad_role_id)")
        )
    with op.batch_alter_table("squad_members") as batch:
        batch.alter_column("role", nullable=False)
        batch.create_check_constraint("ck_squad_members_role", "role in ('member','officer','leader')")
        batch.create_index("ix_squad_members_role", ["role"])
        batch.drop_constraint("fk_squad_members_squad_role_id", type_="foreignkey")
        batch.drop_index("ix_squad_members_squad_role_id")
        batch.drop_column("squad_role_id")

    with op.batch_alter_table("fleet_memberships") as batch:
        batch.add_column(sa.Column("role", sa.String(40), nullable=True))
        batch.add_column(sa.Column("preferred_ships", sa.String(300), nullable=True))
    if not offline:
        bind.execute(
            sa.text("UPDATE fleet_memberships SET role=(SELECT code FROM fleet_roles WHERE id=fleet_memberships.fleet_role_id)")
        )
        preferences: dict[int, list[str]] = defaultdict(list)
        for membership_id, ship_name in bind.execute(
            sa.text(
                "SELECT fleet_membership_id, ship_name FROM fleet_membership_ship_preferences "
                "ORDER BY fleet_membership_id, sort_order"
            )
        ):
            preferences[int(membership_id)].append(str(ship_name))
        for membership_id, names in preferences.items():
            bind.execute(
                sa.text("UPDATE fleet_memberships SET preferred_ships=:ships WHERE id=:id"),
                {"ships": ", ".join(names), "id": membership_id},
            )
    with op.batch_alter_table("fleet_memberships") as batch:
        batch.alter_column("role", nullable=False)
        batch.create_check_constraint(
            "ck_fleet_memberships_role",
            "role in ('member','fleet_lieutenant','fleet_admiral')",
        )
        batch.create_index("ix_fleet_memberships_role", ["role"])
        batch.drop_constraint("fk_fleet_memberships_fleet_role_id", type_="foreignkey")
        batch.drop_index("ix_fleet_memberships_fleet_role_id")
        batch.drop_column("fleet_role_id")
    op.drop_table("fleet_membership_ship_preferences")

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("role", sa.String(32), nullable=True))
    if not offline:
        bind.execute(sa.text("UPDATE users SET role=(SELECT code FROM site_roles WHERE id=users.site_role_id)"))
    with op.batch_alter_table("users") as batch:
        batch.alter_column("role", nullable=False)
        batch.create_check_constraint("ck_users_role", "role in ('user','moderator','admin')")
        batch.create_index("ix_users_role", ["role"])
        batch.drop_constraint("fk_users_site_role_id", type_="foreignkey")
        batch.drop_index("ix_users_site_role_id")
        batch.drop_column("site_role_id")

    op.drop_table("squad_roles")
    op.drop_table("fleet_roles")
    op.drop_table("site_roles")
