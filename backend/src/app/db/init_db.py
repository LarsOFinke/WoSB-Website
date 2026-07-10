from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.seeds import SeedManager
from app.db.base import Base
from app.db.session import engine
from app.modules.registry import register_all_models


def _ensure_sqlite_columns() -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    statements = []

    if "groups" in table_names:
        group_columns = {column["name"] for column in inspector.get_columns("groups")}
        if "fleet_restriction" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN fleet_restriction VARCHAR(120)")
        if "closed_at" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN closed_at DATETIME")
        if "max_ship_rate" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN max_ship_rate INTEGER")
        if "expectations" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN expectations TEXT")
        if "activity_plan" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN activity_plan TEXT")
        if "contact_note" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN contact_note VARCHAR(300)")
        if "scheduled_start_at" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN scheduled_start_at DATETIME")
        if "scheduled_end_at" not in group_columns:
            statements.append("ALTER TABLE groups ADD COLUMN scheduled_end_at DATETIME")

    if "group_members" in table_names:
        group_member_columns = {column["name"] for column in inspector.get_columns("group_members")}
        if "build_id" not in group_member_columns:
            statements.append("ALTER TABLE group_members ADD COLUMN build_id INTEGER")

    if "builds" in table_names:
        build_columns = {column["name"] for column in inspector.get_columns("builds")}
        if "owner_id" not in build_columns:
            statements.append("ALTER TABLE builds ADD COLUMN owner_id INTEGER")

    if "app_logs" in table_names:
        app_log_columns = {column["name"] for column in inspector.get_columns("app_logs")}
        app_log_column_defaults = {
            "client_ip": "VARCHAR(120)",
            "forwarded_for": "VARCHAR(300)",
            "user_agent": "VARCHAR(300)",
            "query_string": "VARCHAR(500)",
        }
        for column_name, ddl in app_log_column_defaults.items():
            if column_name not in app_log_columns:
                statements.append(f"ALTER TABLE app_logs ADD COLUMN {column_name} {ddl}")

    if "ships" in table_names:
        ship_columns = {column["name"] for column in inspector.get_columns("ships")}
        ship_column_defaults = {
            "durability": "INTEGER NOT NULL DEFAULT 0",
            "speed_knots": "FLOAT NOT NULL DEFAULT 0",
            "maneuverability": "FLOAT NOT NULL DEFAULT 0",
            "armor": "FLOAT NOT NULL DEFAULT 0",
            "hold_capacity": "INTEGER NOT NULL DEFAULT 0",
            "displacement_tons": "INTEGER NOT NULL DEFAULT 0",
            "source": "VARCHAR(120)",
        }
        for column_name, ddl in ship_column_defaults.items():
            if column_name not in ship_columns:
                statements.append(f"ALTER TABLE ships ADD COLUMN {column_name} {ddl}")

    if "build_item_options" in table_names:
        option_columns = {column["name"] for column in inspector.get_columns("build_item_options")}
        option_column_defaults = {
            "option_kind": "VARCHAR(40)",
            "weapon_caliber_inches": "FLOAT",
        }
        for column_name, ddl in option_column_defaults.items():
            if column_name not in option_columns:
                statements.append(f"ALTER TABLE build_item_options ADD COLUMN {column_name} {ddl}")

    if "fleet_memberships" in table_names:
        membership_columns = {column["name"] for column in inspector.get_columns("fleet_memberships")}
        if "assignment" not in membership_columns:
            statements.append("ALTER TABLE fleet_memberships ADD COLUMN assignment VARCHAR(120)")
        if "availability" not in membership_columns:
            statements.append("ALTER TABLE fleet_memberships ADD COLUMN availability VARCHAR(240)")
        if "timezone" not in membership_columns:
            statements.append("ALTER TABLE fleet_memberships ADD COLUMN timezone VARCHAR(80)")
        if "discord_handle" not in membership_columns:
            statements.append("ALTER TABLE fleet_memberships ADD COLUMN discord_handle VARCHAR(120)")
        if "admin_note" not in membership_columns:
            statements.append("ALTER TABLE fleet_memberships ADD COLUMN admin_note TEXT")


    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))



def _migrate_user_profiles() -> None:
    """Backfill the normalized user_profiles table from older prototype DBs.

    Existing local SQLite databases may still have profile columns on users.
    New databases use user_profiles from the start.
    """
    if not str(engine.url).startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "users" not in table_names or "user_profiles" not in table_names:
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    display_expr = "COALESCE(NULLIF(display_name, ''), username)" if "display_name" in user_columns else "username"
    fleet_expr = "fleet_name" if "fleet_name" in user_columns else "NULL"
    focus_expr = "preferred_focus" if "preferred_focus" in user_columns else "NULL"
    note_expr = "note" if "note" in user_columns else "NULL"

    with engine.begin() as connection:
        connection.execute(text(f"""
            INSERT INTO user_profiles (user_id, display_name, external_fleet_name, preferred_focus, note, created_at, updated_at)
            SELECT users.id, {display_expr}, {fleet_expr}, {focus_expr}, {note_expr}, users.created_at, users.updated_at
            FROM users
            LEFT JOIN user_profiles ON user_profiles.user_id = users.id
            WHERE user_profiles.user_id IS NULL
        """))


def verify_database_ready() -> None:
    """Fail fast when the configured database or migration state is unavailable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        if settings.database_schema_mode == "migrate":
            connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))


def create_tables() -> None:
    register_all_models()
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
    _migrate_user_profiles()


def seed_database() -> None:
    register_all_models()
    with Session(engine) as db:
        SeedManager(db).run()


def create_and_seed() -> None:
    create_tables()
    seed_database()


def reset_database() -> None:
    if settings.is_production:
        raise RuntimeError("Database reset is disabled in production.")
    register_all_models()
    Base.metadata.drop_all(bind=engine)
    create_and_seed()
