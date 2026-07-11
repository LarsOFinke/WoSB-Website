"""add seed ownership metadata and catalog images

Revision ID: a1b2c3d4e5f6
Revises: 7e4c9b2a1f60
Create Date: 2026-07-11 14:20:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7e4c9b2a1f60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_seed_columns(table: str) -> None:
    with op.batch_alter_table(table) as batch:
        batch.add_column(sa.Column("seed_key", sa.String(220), nullable=True))
        batch.add_column(sa.Column("seed_revision", sa.String(80), nullable=True))
        batch.add_column(sa.Column("seed_checksum", sa.String(64), nullable=True))
        batch.add_column(
            sa.Column("is_seed_overridden", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.create_index(f"ix_{table}_seed_key", ["seed_key"], unique=True)


def _drop_seed_columns(table: str) -> None:
    with op.batch_alter_table(table) as batch:
        batch.drop_index(f"ix_{table}_seed_key")
        batch.drop_column("is_seed_overridden")
        batch.drop_column("seed_checksum")
        batch.drop_column("seed_revision")
        batch.drop_column("seed_key")


def upgrade() -> None:
    _add_seed_columns("build_item_categories")
    _add_seed_columns("build_item_options")
    _add_seed_columns("ships")
    with op.batch_alter_table("build_item_options") as batch:
        batch.add_column(sa.Column("image_url", sa.String(500), nullable=True))
    with op.batch_alter_table("ships") as batch:
        batch.add_column(sa.Column("image_url", sa.String(500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ships") as batch:
        batch.drop_column("image_url")
    with op.batch_alter_table("build_item_options") as batch:
        batch.drop_column("image_url")
    _drop_seed_columns("ships")
    _drop_seed_columns("build_item_options")
    _drop_seed_columns("build_item_categories")
