#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

SCHEMA_VERSION = 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--status", required=True, choices=("running", "succeeded", "failed"))
    parser.add_argument("--stage", required=True)
    parser.add_argument("--reason", default="scheduled")
    parser.add_argument("--message", default="")
    parser.add_argument("--started-at", default="")
    parser.add_argument("--postgres", default="")
    parser.add_argument("--files", default="")
    parser.add_argument("--recovery", default="")
    parser.add_argument("--verification", default="")
    parser.add_argument("--backup-set", default="")
    args = parser.parse_args()
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": args.status,
        "stage": args.stage,
        "reason": args.reason,
        "message": args.message,
        "started_at": args.started_at or now,
        "updated_at": now,
        "finished_at": now if args.status in {"succeeded", "failed"} else "",
        "artifacts": {
            "postgres": args.postgres,
            "files": args.files,
            "recovery": args.recovery,
            "verification": args.verification,
            "backup_set": args.backup_set,
        },
    }
    args.path.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.path.with_name(f".{args.path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(args.path)
    args.path.chmod(0o600)


if __name__ == "__main__":
    main()
