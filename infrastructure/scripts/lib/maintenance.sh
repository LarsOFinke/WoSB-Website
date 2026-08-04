#!/usr/bin/env bash

maintenance_status_dir() {
  printf '%s/data/control/status' "$INFRA_DIR"
}

maintenance_control() {
  local action="$1"
  shift
  maintenance_control_artifact "$action" "$@"
}

maintenance_control_artifact() {
  local action="$1"
  shift
  # Artifact deployments intentionally have no backend checkout on the host.
  # Keep the same filesystem contract as app.cli.maintenance_mode using only
  # the Python standard library.
  python3 - "$action" "$(maintenance_status_dir)" "$INFRA_DIR/data/control/inbox" "$@" <<'PY_MAINTENANCE_ARTIFACT'
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

action, status_dir_arg, event_dir_arg, *extra = sys.argv[1:]
status_dir = Path(status_dir_arg)
event_dir = Path(event_dir_arg)
marker = status_dir / "maintenance-mode.json"
reason = "update"
message = "A server update is being installed."
retry_after = 180
outcome = "succeeded"
for index, value in enumerate(extra):
    if value == "--reason" and index + 1 < len(extra):
        reason = extra[index + 1]
    elif value == "--message" and index + 1 < len(extra):
        message = extra[index + 1]
    elif value == "--retry-after" and index + 1 < len(extra):
        retry_after = int(extra[index + 1])
    elif value == "--outcome" and index + 1 < len(extra):
        outcome = extra[index + 1]

def publish(event_action, event_reason, event_message, started_at, event_outcome):
    event_dir.mkdir(parents=True, exist_ok=True)
    event_id = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "event_id": event_id,
        "action": event_action,
        "reason": event_reason,
        "message": " ".join(event_message.split())[:500],
        "occurred_at": now,
        "started_at": started_at,
        "outcome": event_outcome,
    }
    destination = event_dir / f"maintenance-event-{now.replace('-', '').replace(':', '').replace('+00:00', 'Z')}-{event_id}.json"
    temporary = event_dir / f".{destination.name}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    if os.geteuid() == 0:
        os.chown(temporary, 10001, 10001)
    os.replace(temporary, destination)
    destination.chmod(0o600)

if action == "enable":
    started_at = datetime.now(timezone.utc).isoformat()
    state = {
        "reason": reason,
        "message": " ".join(message.split())[:240],
        "started_at": started_at,
        "retry_after_seconds": max(30, min(retry_after, 3600)),
    }
    status_dir.mkdir(parents=True, exist_ok=True)
    temporary = status_dir / f".maintenance-mode.json.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(0o644)
    os.replace(temporary, marker)
    marker.chmod(0o644)
    publish("started", reason, state["message"], started_at, None)
elif action == "disable":
    started_at = ""
    try:
        state = json.loads(marker.read_text(encoding="utf-8"))
        started_at = str(state.get("started_at") or "")
        reason = str(state.get("reason") or reason)
    except (OSError, ValueError, TypeError):
        state = None
    marker.unlink(missing_ok=True)
    if state is not None:
        publish("ended", reason, message, started_at, outcome)
elif action == "status":
    print("inactive" if not marker.exists() else "active")
else:
    raise SystemExit(f"unsupported maintenance action: {action}")
PY_MAINTENANCE_ARTIFACT
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
    if os.geteuid() == 0:
        os.chown(temporary, 10001, 10001)
    os.replace(temporary, destination)
marker.unlink(missing_ok=True)
PY_MAINTENANCE_FALLBACK
    rm -f "$(maintenance_status_dir)/maintenance-mode.json"
  fi
  MAINTENANCE_ACTIVE=false
}
