"""Add outbound webhook integrations and delivery history.

Revision ID: 6f708192a3b4
Revises: 5e6f708192a3
"""

from alembic import op
import sqlalchemy as sa

revision = "6f708192a3b4"
down_revision = "5e6f708192a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbound_webhooks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("endpoint_url", sa.String(length=1000), nullable=False),
        sa.Column("signing_secret", sa.String(length=160), nullable=False),
        sa.Column("event_types_json", sa.Text(), nullable=False),
        sa.Column("channel_key", sa.String(length=120), nullable=True),
        sa.Column("message_template", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(length=80), nullable=False),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("name", "channel_key", "is_active", "created_at", "updated_at", "created_by_user_id"):
        op.create_index(f"ix_outbound_webhooks_{column}", "outbound_webhooks", [column], unique=False)

    op.create_table(
        "outbound_webhook_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("webhook_id", sa.Integer(), nullable=False),
        sa.Column("delivery_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["webhook_id"], ["outbound_webhooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("delivery_id"),
    )
    for column in (
        "webhook_id",
        "delivery_id",
        "event_type",
        "resource_type",
        "resource_id",
        "status",
        "created_at",
        "last_attempt_at",
        "delivered_at",
    ):
        op.create_index(
            f"ix_outbound_webhook_deliveries_{column}",
            "outbound_webhook_deliveries",
            [column],
            unique=False,
        )
    op.create_index(
        "ix_outbound_webhook_deliveries_webhook_status_created",
        "outbound_webhook_deliveries",
        ["webhook_id", "status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("outbound_webhook_deliveries")
    op.drop_table("outbound_webhooks")
