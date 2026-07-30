"""add configurable legal notice

Revision ID: 0013_legal_notice
Revises: 0012_weapon_performance_profiles
Create Date: 2026-07-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0013_legal_notice"
down_revision: str = "0012_weapon_performance_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "legal_notices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_customized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("provider_name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("legal_form", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("represented_by", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("street", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("postal_code", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("city", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("country", sa.String(length=120), nullable=False, server_default="Deutschland"),
        sa.Column("email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("phone", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("register_name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("register_court", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("register_number", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("vat_id", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("business_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column(
            "supervisory_authority", sa.String(length=500), nullable=False, server_default=""
        ),
        sa.Column(
            "editorial_responsible_name", sa.String(length=200), nullable=False, server_default=""
        ),
        sa.Column(
            "editorial_responsible_street", sa.String(length=200), nullable=False, server_default=""
        ),
        sa.Column(
            "editorial_responsible_postal_code", sa.String(length=32), nullable=False, server_default=""
        ),
        sa.Column(
            "editorial_responsible_city", sa.String(length=120), nullable=False, server_default=""
        ),
        sa.Column(
            "editorial_responsible_country",
            sa.String(length=120),
            nullable=False,
            server_default="Deutschland",
        ),
        sa.Column("dispute_resolution_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("additional_information", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "updated_by_username", sa.String(length=80), nullable=False, server_default="environment"
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="ck_legal_notice_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("legal_notices")
