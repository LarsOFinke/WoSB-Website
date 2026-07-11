"""add append-only cookie consent decisions

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cookie_consent_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consent_key", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("necessary", sa.Boolean(), nullable=False),
        sa.Column("preferences", sa.Boolean(), nullable=False),
        sa.Column("analytics", sa.Boolean(), nullable=False),
        sa.Column("external_media", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cookie_consent_decisions_consent_key", "cookie_consent_decisions", ["consent_key"])
    op.create_index("ix_cookie_consent_decisions_created_at", "cookie_consent_decisions", ["created_at"])
    op.create_index("ix_cookie_consent_decisions_user_id", "cookie_consent_decisions", ["user_id"])
    op.create_index("ix_cookie_consent_key_created", "cookie_consent_decisions", ["consent_key", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_cookie_consent_key_created", table_name="cookie_consent_decisions")
    op.drop_index("ix_cookie_consent_decisions_user_id", table_name="cookie_consent_decisions")
    op.drop_index("ix_cookie_consent_decisions_created_at", table_name="cookie_consent_decisions")
    op.drop_index("ix_cookie_consent_decisions_consent_key", table_name="cookie_consent_decisions")
    op.drop_table("cookie_consent_decisions")
