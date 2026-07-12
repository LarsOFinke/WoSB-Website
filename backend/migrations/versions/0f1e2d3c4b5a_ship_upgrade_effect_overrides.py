"""ship-specific upgrade effects and app-log schema repair

Revision ID: 0f1e2d3c4b5a
Revises: f6a7b8c9d0e1
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0f1e2d3c4b5a"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def _column_names(bind, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(bind, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name) if index.get("name")}


def _repair_app_logs(bind) -> None:
    columns = _column_names(bind, "app_logs")
    if not columns:
        return
    definitions: dict[str, sa.Column] = {
        "created_at": sa.Column("created_at", sa.DateTime(), nullable=True),
        "level": sa.Column("level", sa.String(length=20), nullable=True),
        "logger": sa.Column("logger", sa.String(length=120), nullable=True),
        "message": sa.Column("message", sa.Text(), nullable=True),
        "request_id": sa.Column("request_id", sa.String(length=64), nullable=True),
        "method": sa.Column("method", sa.String(length=12), nullable=True),
        "path": sa.Column("path", sa.String(length=300), nullable=True),
        "status_code": sa.Column("status_code", sa.Integer(), nullable=True),
        "duration_ms": sa.Column("duration_ms", sa.Float(), nullable=True),
        "client": sa.Column("client", sa.String(length=120), nullable=True),
        "client_ip": sa.Column("client_ip", sa.String(length=120), nullable=True),
        "forwarded_for": sa.Column("forwarded_for", sa.String(length=300), nullable=True),
        "user_agent": sa.Column("user_agent", sa.String(length=300), nullable=True),
        "query_string": sa.Column("query_string", sa.String(length=500), nullable=True),
        "exception": sa.Column("exception", sa.Text(), nullable=True),
    }
    for name, column in definitions.items():
        if name not in columns:
            op.add_column("app_logs", column)

    # Older prototype databases can contain rows without the fields required by
    # the current response schema. Backfill them before the staff endpoint reads
    # the table so one legacy row cannot turn the whole log view into HTTP 500.
    bind.execute(
        sa.text(
            "UPDATE app_logs SET "
            "created_at = COALESCE(created_at, CURRENT_TIMESTAMP), "
            "level = COALESCE(level, 'INFO'), "
            "logger = COALESCE(logger, 'legacy'), "
            "message = COALESCE(message, '')"
        )
    )

    indexes = _index_names(bind, "app_logs")
    for name in ("created_at", "level", "logger", "request_id", "method", "path", "status_code", "client_ip"):
        index_name = f"ix_app_logs_{name}"
        if index_name not in indexes:
            op.create_index(index_name, "app_logs", [name], unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    if "ship_upgrade_effect_overrides" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "ship_upgrade_effect_overrides",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("ship_id", sa.Integer(), nullable=False),
            sa.Column("option_id", sa.Integer(), nullable=False),
            sa.Column("effect_key", sa.String(length=80), nullable=False),
            sa.Column("effect_value", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["option_id"], ["build_item_options.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["ship_id"], ["ships.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("ship_id", "option_id", "effect_key", name="uq_ship_upgrade_effect_override"),
        )
        op.create_index("ix_ship_upgrade_effect_overrides_id", "ship_upgrade_effect_overrides", ["id"])
        op.create_index("ix_ship_upgrade_effect_overrides_ship_id", "ship_upgrade_effect_overrides", ["ship_id"])
        op.create_index("ix_ship_upgrade_effect_overrides_option_id", "ship_upgrade_effect_overrides", ["option_id"])
        op.create_index("ix_ship_upgrade_effect_overrides_effect_key", "ship_upgrade_effect_overrides", ["effect_key"])
    _repair_app_logs(bind)


def downgrade() -> None:
    bind = op.get_bind()
    if "ship_upgrade_effect_overrides" in sa.inspect(bind).get_table_names():
        op.drop_index("ix_ship_upgrade_effect_overrides_effect_key", table_name="ship_upgrade_effect_overrides")
        op.drop_index("ix_ship_upgrade_effect_overrides_option_id", table_name="ship_upgrade_effect_overrides")
        op.drop_index("ix_ship_upgrade_effect_overrides_ship_id", table_name="ship_upgrade_effect_overrides")
        op.drop_index("ix_ship_upgrade_effect_overrides_id", table_name="ship_upgrade_effect_overrides")
        op.drop_table("ship_upgrade_effect_overrides")
