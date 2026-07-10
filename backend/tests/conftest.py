from __future__ import annotations

import os
from pathlib import Path
import tempfile


TEST_ROOT = Path(tempfile.gettempdir()) / "royal-blackwater-vanguards-pytest"
TEST_ROOT.mkdir(parents=True, exist_ok=True)
TEST_DATABASE = TEST_ROOT / "test.db"
TEST_DATABASE.unlink(missing_ok=True)
TEST_ENV_FILE = TEST_ROOT / "backend.env"
TEST_ENV_FILE.write_text(
    "\n".join(
        [
            "APP_ENV=development",
            f"DATABASE_URL=sqlite:///{TEST_DATABASE.as_posix()}",
            "DB_SCHEMA_MODE=create",
            f"UPLOAD_DIR={TEST_ROOT / 'uploads'}",
            "CORS_ORIGINS=http://localhost:5173",
            "SESSION_COOKIE_SECURE=false",
            "AUTO_SEED=false",
            "",
        ]
    ),
    encoding="utf-8",
)
os.environ.setdefault("RBV_ENV_FILE", str(TEST_ENV_FILE))
