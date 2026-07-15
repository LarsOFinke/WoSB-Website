#!/usr/bin/env bash
set -Eeuo pipefail

# Print one NUL-delimited value per requested top-level JSON key. Missing or
# invalid files yield empty values so callers can apply their own validation.
json_read_fields() {
  local file="$1"
  shift
  python3 - "$file" "$@" <<'PY' 2>/dev/null || true
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
keys = sys.argv[2:]
payload = {}
if path.is_file():
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            payload = loaded
    except (OSError, json.JSONDecodeError):
        pass

for key in keys:
    value = payload.get(key, "")
    if value is None or isinstance(value, (dict, list)):
        value = ""
    sys.stdout.write(str(value))
    sys.stdout.write("\0")
PY
}
