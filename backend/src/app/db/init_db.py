from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

# Importing models registers all SQLAlchemy metadata before create_all/drop_all.
from app import models  # noqa: F401
from app.db.seeds import SeedManager
from app.db.session import Base, engine


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

    if "builds" in table_names:
        build_columns = {column["name"] for column in inspector.get_columns("builds")}
        if "owner_id" not in build_columns:
            statements.append("ALTER TABLE builds ADD COLUMN owner_id INTEGER")

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

def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
    _migrate_user_profiles()


def create_and_seed() -> None:
    create_tables()
    with Session(engine) as db:
        SeedManager(db).run()


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    create_and_seed()
