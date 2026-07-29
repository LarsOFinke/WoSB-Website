"""Replace general request logs with aggregated IP-ban security signals.

Revision ID: 0006_security_event_minimization
Revises: 0005_webhook_security
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_security_event_minimization"
down_revision: str | None = "0005_webhook_security"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Existing request logs contain data outside the new, narrow purpose. They
    # are deliberately deleted rather than migrated.
    op.drop_table("app_logs")
    op.create_table(
        "security_signal_buckets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("client_ip", sa.String(length=45), nullable=False),
        sa.Column("signal", sa.String(length=32), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "signal IN ('reconnaissance', 'login_failure', 'rate_limit')",
            name="ck_security_signal_buckets_signal",
        ),
        sa.CheckConstraint(
            "event_count >= 1",
            name="ck_security_signal_buckets_count",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "day",
            "client_ip",
            "signal",
            name="uq_security_signal_buckets_day_ip_signal",
        ),
    )
    with op.batch_alter_table("security_signal_buckets") as batch_op:
        batch_op.create_index("ix_security_signal_buckets_id", ["id"], unique=False)
        batch_op.create_index("ix_security_signal_buckets_day", ["day"], unique=False)
        batch_op.create_index(
            "ix_security_signal_buckets_client_ip", ["client_ip"], unique=False
        )
        batch_op.create_index("ix_security_signal_buckets_signal", ["signal"], unique=False)


def downgrade() -> None:
    op.drop_table("security_signal_buckets")
    op.create_table(
        "app_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("logger", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("method", sa.String(length=12), nullable=True),
        sa.Column("path", sa.String(length=300), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("client", sa.String(length=120), nullable=True),
        sa.Column("client_ip", sa.String(length=120), nullable=True),
        sa.Column("forwarded_for", sa.String(length=300), nullable=True),
        sa.Column("user_agent", sa.String(length=300), nullable=True),
        sa.Column("query_string", sa.String(length=500), nullable=True),
        sa.Column("exception", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("app_logs") as batch_op:
        batch_op.create_index("ix_app_logs_id", ["id"], unique=False)
        batch_op.create_index("ix_app_logs_created_at", ["created_at"], unique=False)
        batch_op.create_index("ix_app_logs_level", ["level"], unique=False)
        batch_op.create_index("ix_app_logs_logger", ["logger"], unique=False)
        batch_op.create_index("ix_app_logs_request_id", ["request_id"], unique=False)
        batch_op.create_index("ix_app_logs_method", ["method"], unique=False)
        batch_op.create_index("ix_app_logs_path", ["path"], unique=False)
        batch_op.create_index("ix_app_logs_status_code", ["status_code"], unique=False)
        batch_op.create_index("ix_app_logs_client_ip", ["client_ip"], unique=False)
