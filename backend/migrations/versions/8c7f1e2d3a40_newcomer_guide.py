"""add editable newcomer guide

Revision ID: 8c7f1e2d3a40
Revises: 4873603a6906
Create Date: 2026-07-10 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8c7f1e2d3a40"
down_revision: Union[str, Sequence[str], None] = "4873603a6906"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "newcomer_guide_pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("intro", sa.Text(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "newcomer_guide_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(length=24), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["page_id"], ["newcomer_guide_pages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_newcomer_guide_blocks_id", "newcomer_guide_blocks", ["id"])
    op.create_index("ix_newcomer_guide_blocks_page_id", "newcomer_guide_blocks", ["page_id"])
    op.create_table(
        "newcomer_guide_resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("block_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=24), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=180), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["block_id"], ["newcomer_guide_blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_newcomer_guide_resources_id", "newcomer_guide_resources", ["id"])
    op.create_index("ix_newcomer_guide_resources_block_id", "newcomer_guide_resources", ["block_id"])


def downgrade() -> None:
    op.drop_index("ix_newcomer_guide_resources_block_id", table_name="newcomer_guide_resources")
    op.drop_index("ix_newcomer_guide_resources_id", table_name="newcomer_guide_resources")
    op.drop_table("newcomer_guide_resources")
    op.drop_index("ix_newcomer_guide_blocks_page_id", table_name="newcomer_guide_blocks")
    op.drop_index("ix_newcomer_guide_blocks_id", table_name="newcomer_guide_blocks")
    op.drop_table("newcomer_guide_blocks")
    op.drop_table("newcomer_guide_pages")
