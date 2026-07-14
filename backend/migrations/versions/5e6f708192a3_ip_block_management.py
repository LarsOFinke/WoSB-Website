"""Add staff-managed IP block history.

Revision ID: 5e6f708192a3
Revises: 4d5e6f708192
"""

from alembic import op
import sqlalchemy as sa

revision = "5e6f708192a3"
down_revision = "4d5e6f708192"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ip_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("reason", sa.String(length=240), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(length=80), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("unblocked_at", sa.DateTime(), nullable=True),
        sa.Column("unblocked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("unblocked_by_username", sa.String(length=80), nullable=True),
        sa.Column("unblock_reason", sa.String(length=240), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["unblocked_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "ip_address",
        "created_at",
        "created_by_user_id",
        "created_by_username",
        "expires_at",
        "unblocked_at",
        "unblocked_by_user_id",
    ):
        op.create_index(f"ix_ip_blocks_{column}", "ip_blocks", [column], unique=False)
    op.create_index("ix_ip_blocks_ip_active", "ip_blocks", ["ip_address", "unblocked_at", "expires_at"], unique=False)


def downgrade() -> None:
    op.drop_table("ip_blocks")
