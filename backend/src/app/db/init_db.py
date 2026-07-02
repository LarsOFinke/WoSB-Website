from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.lightweight_migrations import apply_lightweight_migrations
from app.db.seed import seed_database
from app.db.session import engine

# Import models so SQLAlchemy registers metadata before create_all.
from app import models  # noqa: F401


def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)
    apply_lightweight_migrations(engine)
    if settings.seed_on_startup:
        seed_database(db)
