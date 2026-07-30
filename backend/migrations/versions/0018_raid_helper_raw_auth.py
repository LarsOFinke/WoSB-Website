"""Remove obsolete configurable Raid-Helper authorization modes.

Revision ID: 0018_raid_helper_raw_auth
Revises: 0017_raid_helper_leaders
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0018_raid_helper_raw_auth"
down_revision: str = "0017_raid_helper_leaders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Raid-Helper v4 accepts the server API key only as the raw Authorization
    # header value. The configurable mode was both misleading and capable of
    # turning a valid key into a guaranteed HTTP 401 response.
    with op.batch_alter_table("raid_helper_profiles") as batch:
        batch.drop_constraint(
            "ck_raid_helper_profile_authorization_mode",
            type_="check",
        )
        batch.drop_column("authorization_mode")


def downgrade() -> None:
    with op.batch_alter_table("raid_helper_profiles") as batch:
        batch.add_column(
            sa.Column(
                "authorization_mode",
                sa.String(length=24),
                nullable=False,
                server_default="authorization",
            )
        )
        batch.create_check_constraint(
            "ck_raid_helper_profile_authorization_mode",
            "authorization_mode IN ('authorization', 'bearer', 'x-api-key')",
        )
