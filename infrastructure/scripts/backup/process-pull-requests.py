#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

REQUEST_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}\.json$")


def env_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def atomic_json(path: Path, payload: dict[str, object], group_id: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
            handle.write("\n")
        os.chown(name, 0, group_id)
        os.chmod(name, 0o640)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: process-pull-requests.py INFRA_DIR")
    infra = Path(sys.argv[1]).resolve()
    values = env_values(infra / ".env")
    environment = values.get("DEPLOYMENT_ENVIRONMENT", "")
    username = values.get("BACKUP_PULL_EXPORT_USER", "")
    enrollment_id = values.get("BACKUP_PULL_ENROLLMENT_ID", "")
    if environment not in {"test", "production"} or username != f"rbf-backup-controller-{environment}":
        return 0
    import grp

    group_id = grp.getgrnam(username).gr_gid
    root = Path(f"/var/lib/rbf-backup-pull/{environment}")
    requests = root / "requests"
    status = root / "status"
    lock_path = infra / "data/control/run/pull-request.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for request_path in sorted(requests.glob("*.json")):
            if request_path.is_symlink() or not REQUEST_RE.fullmatch(request_path.name):
                continue
            request_id = request_path.stem
            status_path = status / request_path.name
            try:
                if request_path.stat().st_size > 4096:
                    raise ValueError("Request exceeds the bounded protocol size.")
                payload = json.loads(request_path.read_text(encoding="utf-8"))
                if (
                    not isinstance(payload, dict)
                    or payload.get("schema_version") != 1
                    or payload.get("kind") != "rbf-backup-pull-request"
                    or payload.get("request_id") != request_id
                    or payload.get("enrollment_id") != enrollment_id
                ):
                    raise ValueError("Request does not match the pull protocol.")
                atomic_json(
                    status_path,
                    {"schema_version": 1, "kind": "rbf-backup-pull-status", "request_id": request_id,
                     "enrollment_id": enrollment_id, "state": "running",
                     "updated_at": datetime.now(timezone.utc).isoformat()},
                    group_id,
                )
                with tempfile.TemporaryDirectory(prefix="rbf-pull-", dir=infra / "data/control/run") as temp:
                    result_root = Path(temp)
                    result_files = {
                        name: result_root / f"{name}.result"
                        for name in ("postgres", "files", "recovery", "verification", "set")
                    }
                    command = [
                        str(infra / "scripts/backup/run-consistent-backup.sh"),
                        "--reason", "backup-controller", "--include-recovery",
                    ]
                    for name, option in (
                        ("postgres", "--postgres-result"), ("files", "--files-result"),
                        ("recovery", "--recovery-result"), ("verification", "--verification-result"),
                        ("set", "--backup-set-result"),
                    ):
                        command.extend((option, str(result_files[name])))
                    subprocess.run(command, check=True, timeout=4 * 60 * 60)
                    set_path = Path(result_files["set"].read_text(encoding="utf-8").strip())
                atomic_json(
                    status_path,
                    {"schema_version": 1, "kind": "rbf-backup-pull-status", "request_id": request_id,
                     "state": "succeeded", "set_filename": set_path.name,
                     "enrollment_id": enrollment_id,
                     "updated_at": datetime.now(timezone.utc).isoformat()},
                    group_id,
                )
            except Exception:
                atomic_json(
                    status_path,
                    {"schema_version": 1, "kind": "rbf-backup-pull-status", "request_id": request_id,
                     "enrollment_id": enrollment_id, "state": "failed",
                     "updated_at": datetime.now(timezone.utc).isoformat()},
                    group_id,
                )
                raise
            finally:
                request_path.unlink(missing_ok=True)
        cutoff = datetime.now(timezone.utc).timestamp() - 7 * 24 * 60 * 60
        for directory in (status, root / "acknowledgements"):
            for path in directory.glob("*.json"):
                try:
                    if path.is_file() and not path.is_symlink() and path.stat().st_mtime < cutoff:
                        path.unlink()
                except FileNotFoundError:
                    continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
