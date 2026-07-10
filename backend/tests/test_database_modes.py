from pathlib import Path

from app.core.database_mode import DatabaseSchemaMode
from app.core.runtime_paths import normalize_database_url


def test_sqlite_is_kept_as_supported_development_backend(tmp_path: Path) -> None:
    database_url = normalize_database_url("sqlite:///./storage/dev.db", base_dir=tmp_path)

    assert database_url.startswith("sqlite:///")
    assert DatabaseSchemaMode.CREATE.value == "create"


def test_postgresql_url_is_kept_for_production() -> None:
    database_url = "postgresql+psycopg://blackwater:secret@postgres:5432/blackwater"

    assert normalize_database_url(database_url, base_dir=Path.cwd()) == database_url
    assert DatabaseSchemaMode.MIGRATE.value == "migrate"
