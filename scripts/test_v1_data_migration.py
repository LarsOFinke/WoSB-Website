#!/usr/bin/env python3
"""Exercise the v1 cleanup migration against representative pre-v1 content."""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PRE_V1_REVISION = "d4e5f6a7b8c9"


def run_alembic(env: dict[str, str], *args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env=env,
        check=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rbf-v1-migration-") as temporary:
        root = Path(temporary)
        database = root / "migration.db"
        env_file = root / "backend.env"
        env_file.write_text(
            "\n".join(
                [
                    "APP_ENV=development",
                    f"DATABASE_URL=sqlite:///{database.as_posix()}",
                    "DB_SCHEMA_MODE=none",
                    f"UPLOAD_DIR={root / 'uploads'}",
                    f"CONTROL_DIR={root / 'control'}",
                    "CORS_ORIGINS=http://localhost",
                    "SESSION_COOKIE_SECURE=false",
                    "AUTO_SEED=false",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment.update({"PYTHONPATH": "src", "RBF_ENV_FILE": str(env_file)})

        run_alembic(environment, "upgrade", PRE_V1_REVISION)
        with sqlite3.connect(database) as connection:
            connection.execute(
                """
                INSERT INTO newcomer_guide_pages
                    (id, title, intro, updated_by_id, created_at, updated_at)
                VALUES
                    (1, 'New Captain Guide', ?, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    "A curated route from your first login to confident fleet participation. "
                    "Work through the sections in order, ask questions early and check the "
                    "calendar before joining operations.",
                ),
            )
            connection.execute(
                """
                INSERT INTO newcomer_guide_blocks
                    (page_id, block_type, title, body, sort_order)
                VALUES
                    (1, 'text', 'Welcome aboard', 'seeded example', 10),
                    (1, 'text', 'Staff custom block', 'keep this content', 20)
                """
            )
            connection.commit()

        run_alembic(environment, "upgrade", "head")
        run_alembic(environment, "check")

        with sqlite3.connect(database) as connection:
            titles = {
                row[0]
                for row in connection.execute(
                    "SELECT title FROM newcomer_guide_blocks ORDER BY sort_order"
                )
            }
            intro = connection.execute(
                "SELECT intro FROM newcomer_guide_pages WHERE id = 1"
            ).fetchone()[0]
        if titles != {"Staff custom block"}:
            raise SystemExit(f"Unexpected newcomer blocks after v1 cleanup: {titles}")
        if intro != "":
            raise SystemExit("Seeded newcomer intro was not cleared by v1 cleanup migration")

    print("v1 cleanup migration OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
