#!/usr/bin/env bash

maintenance_status_dir() {
  printf '%s/data/control/status' "$INFRA_DIR"
}

maintenance_control() {
  local action="$1"
  shift
  PYTHONPATH="$REPO_ROOT/backend/src" python3 -m app.cli.maintenance_mode \
    "$action" --status-dir "$(maintenance_status_dir)" \
    --event-dir "$INFRA_DIR/data/control/inbox" "$@"
}

maintenance_enable() {
  local reason="$1" retry_after="${2:-120}"
  maintenance_control enable --reason "$reason" --retry-after "$retry_after"
  MAINTENANCE_ACTIVE=true
}

maintenance_disable() {
  local outcome="${1:-succeeded}" message="${2:-Maintenance completed.}"
  if ! maintenance_control disable --outcome "$outcome" --message "$message"; then
    # A code rollback can remove the freshly deployed CLI module while this
    # already-loaded shell function is still running. Preserve the terminal
    # audit event with a stdlib-only fallback before removing the 503 marker.
    python3 - "$(maintenance_status_dir)" "$INFRA_DIR/data/control/inbox" \
      "$outcome" "$message" <<'PY_MAINTENANCE_FALLBACK' || true
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

status_dir = Path(sys.argv[1])
event_dir = Path(sys.argv[2])
outcome = sys.argv[3]
message = sys.argv[4]
marker = status_dir / "maintenance-mode.json"
try:
    state = json.loads(marker.read_text(encoding="utf-8"))
except (OSError, ValueError):
    state = None
if isinstance(state, dict):
    event_id = uuid4().hex
    destination = event_dir / f"maintenance-event-{event_id}.json"
    temporary = event_dir / f".{destination.name}.{os.getpid()}.tmp"
    event_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "event_id": event_id,
        "action": "ended",
        "reason": str(state.get("reason") or "update"),
        "message": message,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "started_at": str(state.get("started_at") or ""),
        "outcome": outcome,
    }
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    os.replace(temporary, destination)
marker.unlink(missing_ok=True)
PY_MAINTENANCE_FALLBACK
    rm -f "$(maintenance_status_dir)/maintenance-mode.json"
  fi
  MAINTENANCE_ACTIVE=false
}
