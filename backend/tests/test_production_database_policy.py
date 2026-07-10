from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _run_config_import(tmp_path: Path, *, database_url: str, schema_mode: str) -> subprocess.CompletedProcess[str]:
    env_file = tmp_path / f"{schema_mode}.env"
    env_file.write_text(
        "\n".join(
            [
                "APP_ENV=production",
                f"DATABASE_URL={database_url}",
                f"DB_SCHEMA_MODE={schema_mode}",
                f"UPLOAD_DIR={tmp_path / 'uploads'}",
                "CORS_ORIGINS=https://blackwater.example",
                "SESSION_COOKIE_SECURE=true",
                "AUTO_SEED=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["BLACKWATER_ENV_FILE"] = str(env_file)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run(
        [sys.executable, "-c", "from app.core.config import settings; print(settings.database_backend)"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_production_rejects_sqlite(tmp_path: Path) -> None:
    result = _run_config_import(
        tmp_path,
        database_url=f"sqlite:///{tmp_path / 'production.db'}",
        schema_mode="migrate",
    )

    assert result.returncode != 0
    assert "requires a PostgreSQL DATABASE_URL" in result.stderr


def test_production_requires_alembic_schema_mode(tmp_path: Path) -> None:
    result = _run_config_import(
        tmp_path,
        database_url="postgresql+psycopg://blackwater:secret@postgres:5432/blackwater",
        schema_mode="none",
    )

    assert result.returncode != 0
    assert "requires DB_SCHEMA_MODE=migrate" in result.stderr


def test_production_accepts_postgresql_migrate_mode(tmp_path: Path) -> None:
    result = _run_config_import(
        tmp_path,
        database_url="postgresql+psycopg://blackwater:secret@postgres:5432/blackwater",
        schema_mode="migrate",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "postgresql"
