from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.modules.registry import register_all_models
from app.db.schema_health import verify_alembic_heads
from app.bootstrap.manager import SeedManager


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


def seed_database(*, restore_seed_defaults: bool = False) -> dict[str, dict[str, int]]:
    register_all_models()
    with Session(engine) as db:
        manager = SeedManager(db)
        restored = (
            manager.restore_repository_seed_defaults()
            if restore_seed_defaults
            else {"categories": 0, "options": 0, "ships": 0}
        )
        manager.run()
        return {
            "restored": restored,
            "preserved": manager.seed_override_counts(),
        }


def create_and_seed(*, restore_seed_defaults: bool = False) -> dict[str, dict[str, int]]:
    create_tables()
    return seed_database(restore_seed_defaults=restore_seed_defaults)


def reset_database() -> None:
    if settings.is_production:
        raise RuntimeError("Database reset is disabled in production.")
    register_all_models()
    Base.metadata.drop_all(bind=engine)
    create_and_seed()
