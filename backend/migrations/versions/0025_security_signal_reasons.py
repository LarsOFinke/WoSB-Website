"""Add aggregated reasons and safe request targets to IP-ban signals.

Revision ID: 0025_security_signal_reasons
Revises: 0024_build_file_attachments
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025_security_signal_reasons"
down_revision: str | None = "0024_build_file_attachments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("security_signal_buckets") as batch_op:
        batch_op.add_column(
            sa.Column(
                "reason",
                sa.String(length=32),
                nullable=False,
                server_default="legacy_aggregate",
            )
        )
        batch_op.add_column(
            sa.Column(
                "request_target",
                sa.String(length=180),
                nullable=False,
                server_default="unknown",
            )
        )
        batch_op.drop_constraint(
            "uq_security_signal_buckets_day_ip_signal", type_="unique"
        )
        batch_op.create_unique_constraint(
            "uq_security_signal_buckets_dimensions",
            ["day", "client_ip", "signal", "reason", "request_target"],
        )

    with op.batch_alter_table("security_signal_buckets") as batch_op:
        batch_op.alter_column("reason", server_default=None)
        batch_op.alter_column("request_target", server_default=None)


def downgrade() -> None:
    # Multiple target buckets can collapse into the historical dimensions.
    # Retaining arbitrary representatives would make counts incorrect, so the
    # short-lived candidate data is deliberately cleared during downgrade.
    op.execute(sa.text("DELETE FROM security_signal_buckets"))
    with op.batch_alter_table("security_signal_buckets") as batch_op:
        batch_op.drop_constraint(
            "uq_security_signal_buckets_dimensions", type_="unique"
        )
        batch_op.create_unique_constraint(
            "uq_security_signal_buckets_day_ip_signal",
            ["day", "client_ip", "signal"],
        )
        batch_op.drop_column("request_target")
        batch_op.drop_column("reason")
