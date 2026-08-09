#!/usr/bin/env bash
set -Eeuo pipefail
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ "$EUID" -eq 0 ]] || { echo "Arming a host operation requires root privileges." >&2; exit 1; }
operation="${1:-}"; shift || true
minutes=10
if (($#)); then
  [[ $# -eq 2 && "$1" == "--minutes" ]] || { echo "Usage: sudo $0 OPERATION [--minutes 1-30]" >&2; exit 2; }
  minutes="$2"
fi
result="$(python3 "$INFRA_DIR/scripts/services/host-operation-approval.py" arm "$INFRA_DIR" "$operation" "$minutes")"
token="$(sed -n '1p' <<<"$result")"; expires="$(sed -n '2p' <<<"$result")"
printf 'One-time approval created for %s.\n\nToken: %s\nValid until: %s\n\nEnter it only in the admin form. It is consumed by the first attempt.\n' "$operation" "$token" "$expires"
