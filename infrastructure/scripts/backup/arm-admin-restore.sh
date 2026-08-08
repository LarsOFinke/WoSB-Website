#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

[[ "$EUID" -eq 0 ]] || die "Arming a database restore requires root privileges."
require_command python3

minutes=10
if [[ $# -gt 0 ]]; then
  [[ $# -eq 2 && "$1" == "--minutes" ]] || die "Usage: sudo $0 [--minutes 1-30]"
  minutes="$2"
fi
[[ "$minutes" =~ ^[0-9]+$ ]] || die "The validity period must be an integer."
(( minutes >= 1 && minutes <= 30 )) || die "The validity period must be between 1 and 30 minutes."

secret_dir="$INFRA_DIR/data/control/secrets"
approval_file="$secret_dir/database-restore-approval.json"
install -d -m 0700 -o root -g root "$secret_dir"

result="$(python3 - "$approval_file" "$minutes" <<'PY'
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

path = Path(sys.argv[1])
minutes = int(sys.argv[2])
token = secrets.token_urlsafe(24)
expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
payload = {
    "purpose": "database_restore",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "expires_at": expires_at.isoformat(),
    "token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
}
temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
with temporary.open("x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())
os.chmod(temporary, 0o600)
os.replace(temporary, path)
print(token)
print(expires_at.isoformat())
PY
)"

token="$(printf '%s\n' "$result" | sed -n '1p')"
expires_at="$(printf '%s\n' "$result" | sed -n '2p')"
cat <<EOF
One-time database restore approval created.

Token: $token
Valid until: $expires_at

Enter the token only in the bootstrap-admin form.
It expires after one restore attempt or, at the latest, when the time limit is reached.
EOF
