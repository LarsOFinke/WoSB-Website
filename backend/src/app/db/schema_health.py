from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection

from app.core.config import BACKEND_ROOT


class DatabaseSchemaMismatchError(RuntimeError):
    pass


def expected_alembic_heads(backend_root: Path = BACKEND_ROOT) -> frozenset[str]:
    configuration = Config(str(backend_root / "alembic.ini"))
    scripts = ScriptDirectory.from_config(configuration)
    return frozenset(scripts.get_heads())


def current_alembic_heads(connection: Connection) -> frozenset[str]:
    context = MigrationContext.configure(connection)
    return frozenset(context.get_current_heads())


def verify_alembic_heads(connection: Connection) -> None:
    expected = expected_alembic_heads()
    current = current_alembic_heads(connection)
    if current != expected:
        raise DatabaseSchemaMismatchError(
            "Database schema revision does not match the application Alembic head. "
            f"current={sorted(current)!r} expected={sorted(expected)!r}"
        )
