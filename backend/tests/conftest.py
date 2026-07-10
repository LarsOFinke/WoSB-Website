from __future__ import annotations

import os
from pathlib import Path
import tempfile


TEST_ENV_FILE = Path(tempfile.gettempdir()) / "iron-crown-fleet-hub-pytest.env"
TEST_ENV_FILE.write_text(
    "\n".join(
        [
            "APP_ENV=development",
            "DATABASE_URL=sqlite:///:memory:",
            f"UPLOAD_DIR={Path(tempfile.gettempdir()) / 'iron-crown-fleet-hub-uploads'}",
            "CORS_ORIGINS=http://localhost:5173",
            "SESSION_COOKIE_SECURE=false",
            "AUTO_SEED=false",
            "",
        ]
    ),
    encoding="utf-8",
)
os.environ.setdefault("WOSB_ENV_FILE", str(TEST_ENV_FILE))
