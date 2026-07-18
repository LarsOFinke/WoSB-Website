"""add normalized build discovery classifications

Revision ID: 0002_build_discovery
Revises: 0001_baseline
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_build_discovery"
down_revision: Union[str, Sequence[str], None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "build_classifications",
        sa.Column("build_id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["builds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("build_id", "tag"),
    )
    op.create_index(
        "ix_build_classifications_tag_build_id",
        "build_classifications",
        ["tag", "build_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_build_classifications_tag_build_id",
        table_name="build_classifications",
    )
    op.drop_table("build_classifications")
