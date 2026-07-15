#!/usr/bin/env bash
set -Eeuo pipefail

now_iso() {
  date --iso-8601=seconds
}

update_status_write() {
  local state="$1" message="$2" started_at="${3:-}" finished_at="${4:-}" before="${5:-}" after="${6:-}"
  STATE="$state" \
  OPERATION="$OPERATION" \
  MESSAGE="$message" \
  REQUESTED_BY="$REQUESTED_BY" \
  REQUESTED_AT="${REQUESTED_AT:-}" \
  STARTED_AT="$started_at" \
  FINISHED_AT="$finished_at" \
  COMMIT_BEFORE="$before" \
  COMMIT_AFTER="$after" \
  STATUS_FILE="$STATUS_FILE" \
  python3 <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

path = Path(os.environ["STATUS_FILE"])
try:
    old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
except (OSError, json.JSONDecodeError):
    old = {}

payload = {
    "state": os.environ["STATE"],
    "operation": os.environ.get("OPERATION") or old.get("operation") or "update",
    "message": os.environ["MESSAGE"],
    "requested_by": os.environ.get("REQUESTED_BY") or old.get("requested_by"),
    "requested_at": os.environ.get("REQUESTED_AT") or old.get("requested_at") or datetime.now(timezone.utc).isoformat(),
    "started_at": os.environ.get("STARTED_AT") or old.get("started_at"),
    "finished_at": os.environ.get("FINISHED_AT") or None,
    "commit_before": os.environ.get("COMMIT_BEFORE") or old.get("commit_before"),
    "commit_after": os.environ.get("COMMIT_AFTER") or old.get("commit_after"),
}
temporary = path.with_name(f".{path.name}.tmp")
temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
temporary.replace(path)
path.chmod(0o644)
PY
}
