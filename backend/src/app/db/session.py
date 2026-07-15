from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.configuration.models import Settings
from app.core.config import settings


@dataclass(slots=True)
class DatabaseSessionFactory:
    engine: Engine
    session_maker: sessionmaker[Session]

    @classmethod
    def from_settings(cls, application_settings: Settings) -> "DatabaseSessionFactory":
        is_sqlite = application_settings.database_backend == "sqlite"
        engine = create_engine(
            application_settings.database_url,
            connect_args={"check_same_thread": False} if is_sqlite else {},
            pool_pre_ping=not is_sqlite,
        )
        maker = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        return cls(engine=engine, session_maker=maker)

    def dependency(self) -> Generator[Session, None, None]:
        with self.session_maker() as db:
            yield db


database_sessions = DatabaseSessionFactory.from_settings(settings)
engine = database_sessions.engine
SessionLocal = database_sessions.session_maker


def get_db() -> Generator[Session, None, None]:
    yield from database_sessions.dependency()


__all__ = [
    "DatabaseSessionFactory",
    "SessionLocal",
    "database_sessions",
    "engine",
    "get_db",
]
