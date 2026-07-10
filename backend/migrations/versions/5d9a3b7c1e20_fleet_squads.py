"""add fleet squads and squad calendar scope

Revision ID: 5d9a3b7c1e20
Revises: 8c7f1e2d3a40
Create Date: 2026-07-10 18:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "5d9a3b7c1e20"
down_revision: Union[str, Sequence[str], None] = "8c7f1e2d3a40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "squads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fleet_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("focus", sa.String(length=160), nullable=True),
        sa.Column("max_members", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fleet_id", "name", name="uq_squads_fleet_name"),
        sa.UniqueConstraint("fleet_id", "slug", name="uq_squads_fleet_slug"),
    )
    op.create_index("ix_squads_id", "squads", ["id"])
    op.create_index("ix_squads_fleet_id", "squads", ["fleet_id"])
    op.create_index("ix_squads_name", "squads", ["name"])
    op.create_index("ix_squads_slug", "squads", ["slug"])
    op.create_index("ix_squads_is_active", "squads", ["is_active"])
    op.create_index("ix_squads_created_by_id", "squads", ["created_by_id"])

    op.create_table(
        "squad_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("squad_id", sa.Integer(), nullable=False),
        sa.Column("fleet_membership_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("role in ('member', 'officer', 'leader')", name="ck_squad_members_role"),
        sa.ForeignKeyConstraint(["fleet_membership_id"], ["fleet_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["squad_id"], ["squads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("squad_id", "fleet_membership_id", name="uq_squad_members_membership"),
    )
    op.create_index("ix_squad_members_id", "squad_members", ["id"])
    op.create_index("ix_squad_members_squad_id", "squad_members", ["squad_id"])
    op.create_index("ix_squad_members_fleet_membership_id", "squad_members", ["fleet_membership_id"])
    op.create_index("ix_squad_members_role", "squad_members", ["role"])

    with op.batch_alter_table("fleet_events") as batch_op:
        batch_op.add_column(sa.Column("squad_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_fleet_events_squad_id_squads",
            "squads",
            ["squad_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_fleet_events_squad_id", ["squad_id"])


def downgrade() -> None:
    with op.batch_alter_table("fleet_events") as batch_op:
        batch_op.drop_index("ix_fleet_events_squad_id")
        batch_op.drop_constraint("fk_fleet_events_squad_id_squads", type_="foreignkey")
        batch_op.drop_column("squad_id")

    op.drop_index("ix_squad_members_role", table_name="squad_members")
    op.drop_index("ix_squad_members_fleet_membership_id", table_name="squad_members")
    op.drop_index("ix_squad_members_squad_id", table_name="squad_members")
    op.drop_index("ix_squad_members_id", table_name="squad_members")
    op.drop_table("squad_members")

    op.drop_index("ix_squads_created_by_id", table_name="squads")
    op.drop_index("ix_squads_is_active", table_name="squads")
    op.drop_index("ix_squads_slug", table_name="squads")
    op.drop_index("ix_squads_name", table_name="squads")
    op.drop_index("ix_squads_fleet_id", table_name="squads")
    op.drop_index("ix_squads_id", table_name="squads")
    op.drop_table("squads")
