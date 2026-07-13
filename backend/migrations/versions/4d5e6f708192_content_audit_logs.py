"""Add staff-visible content audit logs.

Revision ID: 4d5e6f708192
Revises: 3c4d5e6f7081
"""

from alembic import op
import sqlalchemy as sa

revision = "4d5e6f708192"
down_revision = "3c4d5e6f7081"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_username", sa.String(length=80), nullable=False),
        sa.Column("actor_role", sa.String(length=32), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=24), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("changed_fields_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("created_at", "actor_user_id", "actor_username", "actor_role", "entity_type", "entity_id", "action"):
        op.create_index(f"ix_audit_logs_{column}", "audit_logs", [column], unique=False)
    op.create_index("ix_audit_logs_entity_time", "audit_logs", ["entity_type", "created_at"], unique=False)
    op.create_index("ix_app_logs_created_ip", "app_logs", ["created_at", "client_ip"], unique=False)
    op.create_index("ix_app_logs_status_created", "app_logs", ["status_code", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_app_logs_status_created", table_name="app_logs")
    op.drop_index("ix_app_logs_created_ip", table_name="app_logs")
    op.drop_table("audit_logs")
