"""Add privacy contact inbox.

Revision ID: 0022_privacy_contact_requests
Revises: 0021_data_subject_requests
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0022_privacy_contact_requests"
down_revision: str = "0021_data_subject_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "privacy_contact_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("reply_email", sa.String(254), nullable=False),
        sa.Column("subject", sa.String(160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("handled_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["handled_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_privacy_contact_requests_user_id", "privacy_contact_requests", ["user_id"])
    op.create_index("ix_privacy_contact_requests_status", "privacy_contact_requests", ["status"])
    op.create_index(
        "ix_privacy_contact_requests_created_at", "privacy_contact_requests", ["created_at"]
    )


def downgrade() -> None:
    op.drop_table("privacy_contact_requests")
