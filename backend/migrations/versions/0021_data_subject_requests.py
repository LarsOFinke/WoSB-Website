"""Add auditable data-subject correction and deletion requests.

Revision ID: 0021_data_subject_requests
Revises: 0020_raid_helper_premium
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0021_data_subject_requests"
down_revision: str = "0020_raid_helper_premium"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "data_subject_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("handled_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["handled_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_data_subject_requests_subject_user_id", "data_subject_requests", ["subject_user_id"]
    )
    op.create_index(
        "ix_data_subject_requests_request_type", "data_subject_requests", ["request_type"]
    )
    op.create_index("ix_data_subject_requests_status", "data_subject_requests", ["status"])
    op.create_index("ix_data_subject_requests_created_at", "data_subject_requests", ["created_at"])


def downgrade() -> None:
    op.drop_table("data_subject_requests")
