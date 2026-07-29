"""Add build upvotes and moderator-managed build roles.

Revision ID: 0007_build_votes_and_roles
Revises: 0006_security_event_minimization
"""

from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision: str = "0007_build_votes_and_roles"
down_revision: str | None = "0006_security_event_minimization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_DEFAULT_ROLES = (
    ("balanced", "Balanced", "General-purpose build with no single dominant specialization.", 10),
    ("boarding", "Boarding", "Build focused on boarding pressure and close-range crew combat.", 20),
    ("gunnery", "Gunnery", "Build focused on weapon performance and ranged damage.", 30),
    ("defensive", "Defensive", "Build focused on survivability, sustain and damage mitigation.", 40),
)


def upgrade() -> None:
    op.create_table(
        "build_roles",
        sa.Column("slug", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("slug"),
    )
    op.create_index("ix_build_roles_sort_order", "build_roles", ["sort_order"], unique=False)

    role_table = sa.table(
        "build_roles",
        sa.column("slug", sa.String()),
        sa.column("label", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    op.bulk_insert(
        role_table,
        [
            {
                "slug": slug,
                "label": label,
                "description": description,
                "sort_order": sort_order,
                "created_at": now,
                "updated_at": now,
            }
            for slug, label, description, sort_order in _DEFAULT_ROLES
        ],
        multiinsert=False,
    )

    with op.batch_alter_table("builds") as batch_op:
        batch_op.create_foreign_key(
            "fk_builds_build_type_build_roles",
            "build_roles",
            ["build_type"],
            ["slug"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        )

    op.create_table(
        "build_votes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("build_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["builds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("build_id", "user_id", name="uq_build_votes_build_user"),
    )
    op.create_index("ix_build_votes_id", "build_votes", ["id"], unique=False)
    op.create_index("ix_build_votes_build_id", "build_votes", ["build_id"], unique=False)
    op.create_index("ix_build_votes_user_id", "build_votes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_build_votes_user_id", table_name="build_votes")
    op.drop_index("ix_build_votes_build_id", table_name="build_votes")
    op.drop_index("ix_build_votes_id", table_name="build_votes")
    op.drop_table("build_votes")

    with op.batch_alter_table("builds") as batch_op:
        batch_op.drop_constraint("fk_builds_build_type_build_roles", type_="foreignkey")

    op.drop_index("ix_build_roles_sort_order", table_name="build_roles")
    op.drop_table("build_roles")
