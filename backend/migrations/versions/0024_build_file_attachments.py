"""Track files owned by builds for complete deletion.

Revision ID: 0024_build_file_attachments
Revises: 0023_build_printouts
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0024_build_file_attachments"
down_revision: str = "0023_build_printouts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "build_file_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("build_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["builds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["stored_files.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("build_id", "file_id", name="uq_build_file_attachment"),
    )
    op.create_index("ix_build_file_attachments_id", "build_file_attachments", ["id"])
    op.create_index("ix_build_file_attachments_build_id", "build_file_attachments", ["build_id"])
    op.create_index("ix_build_file_attachments_file_id", "build_file_attachments", ["file_id"])


def downgrade() -> None:
    op.drop_table("build_file_attachments")
