from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.core.config_error import ConfigError


def resolve_runtime_path(value: str, *, base_dir: Path, setting_name: str) -> Path:
    raw_value = value.strip()
    if os.name == "nt" and raw_value.startswith("/"):
        raise ConfigError(
            f"{setting_name} uses a POSIX absolute path ({raw_value!r}) on Windows. "
            "Use a Windows path or a repository-relative path instead."
        )

    path = Path(raw_value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def normalize_database_url(database_url: str, *, base_dir: Path) -> str:
    try:
        url = make_url(database_url)
    except ArgumentError as exc:
        raise ConfigError(f"DATABASE_URL is invalid: {exc}") from exc

    if url.get_backend_name() != "sqlite":
        return database_url

    database = url.database
    if not database or database == ":memory:" or database.startswith("file:"):
        return database_url

    database_path = resolve_runtime_path(
        database,
        base_dir=base_dir,
        setting_name="DATABASE_URL",
    )
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigError(
            f"Cannot create the SQLite database directory {database_path.parent}. "
            "Check DATABASE_URL and directory permissions."
        ) from exc

    return url.set(database=database_path.as_posix()).render_as_string(hide_password=False)
