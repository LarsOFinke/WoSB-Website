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

    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "fleet_name" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN fleet_name VARCHAR(120)")
        if "fleet_id" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN fleet_id INTEGER")
        if "preferred_focus" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN preferred_focus VARCHAR(80)")
        if "note" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN note TEXT")

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

    if "build_item_options" in table_names:
        option_columns = {column["name"] for column in inspector.get_columns("build_item_options")}
        if "stat_effects" not in option_columns:
            statements.append("ALTER TABLE build_item_options ADD COLUMN stat_effects TEXT")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def create_and_seed() -> None:
    create_tables()
    with Session(engine) as db:
        SeedManager(db).run()


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    create_and_seed()
