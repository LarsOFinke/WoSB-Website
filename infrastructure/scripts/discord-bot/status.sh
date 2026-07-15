#!/usr/bin/env bash
set -Eeuo pipefail

discord_bot_status_write() {
  local state="$1" operation="$2" message="$3"
  local requested_by="${4:-}" requested_at="${5:-}" started_at="${6:-}" finished_at="${7:-}"

  STATE="$state" \
  OPERATION="$operation" \
  MESSAGE="$message" \
  REQUESTED_BY="$requested_by" \
  REQUESTED_AT="$requested_at" \
  STARTED_AT="$started_at" \
  FINISHED_AT="$finished_at" \
  CONFIGURED="$([[ -n "$REPO_URL" ]] && echo true || echo false)" \
  INSTALLED="$(discord_bot_is_installed && echo true || echo false)" \
  SERVICE_STATE="$(discord_bot_service_state)" \
  VERSION_VALUE="$(discord_bot_version)" \
  COMMIT_VALUE="$(discord_bot_commit)" \
  STATUS_FILE="$STATUS_FILE" \
  CONFIG_SUMMARY_FILE="$CONFIG_SUMMARY_FILE" \
  python3 <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["STATUS_FILE"])
summary_path = Path(os.environ["CONFIG_SUMMARY_FILE"])
configuration = {}
if summary_path.is_file():
    try:
        loaded = json.loads(summary_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            configuration = loaded
    except (OSError, json.JSONDecodeError):
        configuration = {"valid": False, "message": "Configuration summary could not be read."}

payload = {
    "state": os.environ["STATE"],
    "operation": os.environ["OPERATION"],
    "message": os.environ["MESSAGE"],
    "configured": os.environ["CONFIGURED"] == "true",
    "installed": os.environ["INSTALLED"] == "true",
    "service_state": os.environ["SERVICE_STATE"] or "unknown",
    "version": os.environ["VERSION_VALUE"] or None,
    "commit": os.environ["COMMIT_VALUE"] or None,
    "requested_by": os.environ["REQUESTED_BY"] or None,
    "requested_at": os.environ["REQUESTED_AT"] or None,
    "started_at": os.environ["STARTED_AT"] or None,
    "finished_at": os.environ["FINISHED_AT"] or None,
    "configuration": configuration,
}
temporary = path.with_name("." + path.name + ".tmp")
temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
temporary.replace(path)
path.chmod(0o664)
PY
}
