"""Add one cached public printout per build.

Revision ID: 0023_build_printouts
Revises: 0022_privacy_contact_requests
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0023_build_printouts"
down_revision: str = "0022_privacy_contact_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("builds", sa.Column("printout_checksum", sa.String(64), nullable=True))
    op.add_column("builds", sa.Column("printout_size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("builds", sa.Column("printout_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("builds", "printout_updated_at")
    op.drop_column("builds", "printout_size_bytes")
    op.drop_column("builds", "printout_checksum")
