#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        raise SystemExit("usage: wait-for-pull-ack.py INFRA_DIR SET_MANIFEST [TIMEOUT_SECONDS]")
    infra = Path(sys.argv[1]).resolve()
    manifest = Path(sys.argv[2]).resolve(strict=True)
    values = read_env(infra / ".env")
    try:
        timeout = int(sys.argv[3]) if len(sys.argv) == 4 else int(
            values.get("BACKUP_PULL_ACK_TIMEOUT_SECONDS", "300")
        )
    except ValueError as exc:
        raise SystemExit("Backup acknowledgement timeout must be an integer.") from exc
    if not 30 <= timeout <= 3600:
        raise SystemExit("Backup acknowledgement timeout must be between 30 and 3600 seconds.")
    environment = values.get("DEPLOYMENT_ENVIRONMENT", "")
    enrollment_id = values.get("BACKUP_PULL_ENROLLMENT_ID", "")
    if not enrollment_id:
        return 0
    acknowledgement = Path(
        f"/var/lib/rbf-backup-pull/{environment}/acknowledgements/{manifest.name}.ack.json"
    )
    expected = hashlib.sha256(manifest.read_bytes()).hexdigest()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if acknowledgement.is_file() and not acknowledgement.is_symlink() and acknowledgement.stat().st_size <= 4096:
                payload = json.loads(acknowledgement.read_text(encoding="utf-8"))
                if (
                    payload.get("kind") == "rbf-backup-pull-acknowledgement"
                    and payload.get("enrollment_id") == enrollment_id
                    and payload.get("set_filename") == manifest.name
                    and payload.get("set_sha256") == expected
                ):
                    acknowledgement.unlink()
                    return 0
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        time.sleep(5)
    raise SystemExit("Backup controller did not acknowledge the verified pre-update backup in time.")


if __name__ == "__main__":
    raise SystemExit(main())
