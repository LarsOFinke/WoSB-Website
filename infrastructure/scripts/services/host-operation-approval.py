#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import stat

OPERATIONS = {
    "apply_enrollment", "backup", "configure", "delete_configuration", "discover",
    "prepare_enrollment", "prepare_key", "restart", "rollback", "scan_local_backups",
    "test", "update",
}


def approval_path(infra_dir: Path, operation: str) -> Path:
    return infra_dir / "data/control/secrets" / f"host-operation-{operation}.json"


def arm(infra_dir: Path, operation: str, minutes: int) -> None:
    if operation not in OPERATIONS:
        raise SystemExit("Unsupported host operation.")
    if not 1 <= minutes <= 30:
        raise SystemExit("Validity must be between 1 and 30 minutes.")
    path = approval_path(infra_dir, operation)
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    token = secrets.token_urlsafe(24)
    current = datetime.now(timezone.utc)
    expires = current + timedelta(minutes=minutes)
    payload = {
        "purpose": "host_operation", "operation": operation,
        "created_at": current.isoformat(), "expires_at": expires.isoformat(),
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
    }
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, (json.dumps(payload, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    print(token)
    print(expires.isoformat())


def consume(infra_dir: Path, operation: str, supplied_hash: str) -> None:
    if operation not in OPERATIONS:
        raise SystemExit("Unsupported host operation.")
    path = approval_path(infra_dir, operation)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0:
            raise SystemExit("Host approval is not a root-owned regular file.")
        if stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_size > 4096:
            raise SystemExit("Host approval permissions or size are invalid.")
        payload = json.loads(os.read(descriptor, 4097).decode())
    finally:
        os.close(descriptor)
        path.unlink(missing_ok=True)
    expires = datetime.fromisoformat(str(payload.get("expires_at", "")).replace("Z", "+00:00"))
    valid = payload.get("purpose") == "host_operation" and payload.get("operation") == operation
    valid = valid and datetime.now(timezone.utc) <= expires
    valid = valid and hmac.compare_digest(str(payload.get("token_sha256", "")), supplied_hash)
    if not valid:
        raise SystemExit("Host approval is invalid, expired, or belongs to another operation.")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    arm_parser = subparsers.add_parser("arm")
    arm_parser.add_argument("infra_dir", type=Path)
    arm_parser.add_argument("operation", choices=sorted(OPERATIONS))
    arm_parser.add_argument("minutes", type=int)
    consume_parser = subparsers.add_parser("consume")
    consume_parser.add_argument("infra_dir", type=Path)
    consume_parser.add_argument("operation", choices=sorted(OPERATIONS))
    consume_parser.add_argument("token_sha256")
    args = parser.parse_args()
    if args.command == "arm":
        arm(args.infra_dir.resolve(), args.operation, args.minutes)
    else:
        consume(args.infra_dir.resolve(), args.operation, args.token_sha256)


if __name__ == "__main__":
    main()
