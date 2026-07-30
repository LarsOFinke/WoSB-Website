"""Add bootstrap-admin capability and explicit file visibility.

Revision ID: 0015_bootstrap_admin_files
Revises: 0014_raid_helper_calendar
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0015_bootstrap_admin_files"
down_revision: str = "0014_raid_helper_calendar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("is_bootstrap_admin", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.create_index("ix_users_is_bootstrap_admin", ["is_bootstrap_admin"], unique=False)

    op.execute(
        sa.text(
            """
            UPDATE users
            SET is_bootstrap_admin = true
            WHERE id = (
                SELECT users.id
                FROM users
                JOIN site_roles ON site_roles.id = users.site_role_id
                WHERE site_roles.code = 'admin' AND users.is_active = true
                ORDER BY users.id
                LIMIT 1
            )
            """
        )
    )

    with op.batch_alter_table("stored_files") as batch_op:
        batch_op.add_column(
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.create_index("ix_stored_files_is_public", ["is_public"], unique=False)

    op.execute(
        sa.text(
            """
            UPDATE stored_files
            SET is_public = true
            WHERE usage_context = 'master-data'
               OR id IN (SELECT file_id FROM forum_post_attachments)
               OR id IN (
                   SELECT guide_attachments.file_id
                   FROM guide_attachments
                   JOIN guides ON guides.id = guide_attachments.guide_id
                   WHERE guides.is_published = true
               )
            """
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("stored_files") as batch_op:
        batch_op.drop_index("ix_stored_files_is_public")
        batch_op.drop_column("is_public")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_is_bootstrap_admin")
        batch_op.drop_column("is_bootstrap_admin")
