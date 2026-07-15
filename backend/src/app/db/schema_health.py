from __future__ import annotations

import os
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection

from app.core.config import BACKEND_ROOT


ALEMBIC_CONFIG_ENV = "RBF_ALEMBIC_CONFIG"


class DatabaseSchemaMismatchError(RuntimeError):
    pass


def resolve_alembic_config_path(backend_root: Path = BACKEND_ROOT) -> Path:
    configured = os.environ.get(ALEMBIC_CONFIG_ENV, "").strip()
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file():
            raise RuntimeError(
                f"{ALEMBIC_CONFIG_ENV} points to a missing Alembic configuration: {path}"
            )
        return path.resolve()

    candidates = (
        backend_root / "alembic.ini",
        Path.cwd() / "alembic.ini",
        Path("/app/alembic.ini"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise RuntimeError(
        "Alembic configuration could not be located. "
        f"Set {ALEMBIC_CONFIG_ENV} explicitly. Searched: {searched}"
    )


def expected_alembic_heads(backend_root: Path = BACKEND_ROOT) -> frozenset[str]:
    configuration = Config(str(resolve_alembic_config_path(backend_root)))
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
