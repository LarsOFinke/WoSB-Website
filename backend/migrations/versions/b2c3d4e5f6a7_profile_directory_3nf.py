"""move fleet directory details into normalized user profiles

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch:
        batch.add_column(sa.Column("availability", sa.String(length=240), nullable=True))
        batch.add_column(sa.Column("timezone", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("discord_handle", sa.String(length=120), nullable=True))

    op.create_table(
        "user_profile_ship_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("ship_id", sa.Integer(), sa.ForeignKey("ships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "ship_id", name="uq_user_profile_ship_preference"),
    )
    op.create_index("ix_user_profile_ship_preferences_user_id", "user_profile_ship_preferences", ["user_id"])
    op.create_index("ix_user_profile_ship_preferences_ship_id", "user_profile_ship_preferences", ["ship_id"])

    op.create_table(
        "user_profile_role_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("fleet_role_id", sa.Integer(), sa.ForeignKey("fleet_roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "fleet_role_id", name="uq_user_profile_role_preference"),
    )
    op.create_index("ix_user_profile_role_preferences_user_id", "user_profile_role_preferences", ["user_id"])
    op.create_index("ix_user_profile_role_preferences_fleet_role_id", "user_profile_role_preferences", ["fleet_role_id"])

    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE user_profiles
        SET availability = (SELECT fm.availability FROM fleet_memberships fm WHERE fm.user_id = user_profiles.user_id),
            timezone = (SELECT fm.timezone FROM fleet_memberships fm WHERE fm.user_id = user_profiles.user_id),
            discord_handle = (SELECT fm.discord_handle FROM fleet_memberships fm WHERE fm.user_id = user_profiles.user_id)
        WHERE EXISTS (SELECT 1 FROM fleet_memberships fm WHERE fm.user_id = user_profiles.user_id)
    """))
    connection.execute(sa.text("""
        INSERT INTO user_profile_ship_preferences (user_id, ship_id, sort_order)
        SELECT fm.user_id, s.id, fsp.sort_order
        FROM fleet_membership_ship_preferences fsp
        JOIN fleet_memberships fm ON fm.id = fsp.fleet_membership_id
        JOIN ships s ON lower(s.name) = lower(fsp.ship_name)
    """))

    op.drop_table("fleet_membership_ship_preferences")
    with op.batch_alter_table("fleet_memberships") as batch:
        batch.drop_column("availability")
        batch.drop_column("timezone")
        batch.drop_column("discord_handle")


def downgrade() -> None:
    with op.batch_alter_table("fleet_memberships") as batch:
        batch.add_column(sa.Column("availability", sa.String(length=240), nullable=True))
        batch.add_column(sa.Column("timezone", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("discord_handle", sa.String(length=120), nullable=True))

    op.create_table(
        "fleet_membership_ship_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fleet_membership_id", sa.Integer(), sa.ForeignKey("fleet_memberships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ship_name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("fleet_membership_id", "ship_name", name="uq_fleet_membership_ship_preference"),
    )
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE fleet_memberships
        SET availability = (SELECT up.availability FROM user_profiles up WHERE up.user_id = fleet_memberships.user_id),
            timezone = (SELECT up.timezone FROM user_profiles up WHERE up.user_id = fleet_memberships.user_id),
            discord_handle = (SELECT up.discord_handle FROM user_profiles up WHERE up.user_id = fleet_memberships.user_id)
    """))
    connection.execute(sa.text("""
        INSERT INTO fleet_membership_ship_preferences (fleet_membership_id, ship_name, sort_order)
        SELECT fm.id, s.name, pref.sort_order
        FROM user_profile_ship_preferences pref
        JOIN fleet_memberships fm ON fm.user_id = pref.user_id
        JOIN ships s ON s.id = pref.ship_id
    """))
    op.drop_table("user_profile_role_preferences")
    op.drop_table("user_profile_ship_preferences")
    with op.batch_alter_table("user_profiles") as batch:
        batch.drop_column("availability")
        batch.drop_column("timezone")
        batch.drop_column("discord_handle")
