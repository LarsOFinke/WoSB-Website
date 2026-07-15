from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.modules.registry import register_all_models
from app.db.schema_health import verify_alembic_heads
from app.seeds import SeedManager


def verify_database_ready() -> None:
    """Fail fast when the configured database or schema state is unavailable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        if settings.database_schema_mode == "migrate":
            verify_alembic_heads(connection)


def create_tables() -> None:
    """Create the current schema for disposable local and test databases."""
    register_all_models()
    Base.metadata.create_all(bind=engine)


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
