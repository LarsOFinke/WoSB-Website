#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
target_env="${1:?target environment path required}"
target_credentials="${2:?target credentials path required}"
source "$INFRA_DIR/scripts/lib/env.sh"
export ENV_FILE="$target_env"
install -d -m 0700 "$(dirname "$target_env")"
if [[ ! -f "$target_env" ]]; then
  initialize_env "" "" false admin "RBF Command" auto "" false
  install -m 0600 "$INFRA_DIR/first-run-credentials.txt" "$target_credentials"
  echo "[website] Neue Environment-Datei und First-Run-Zugangsdaten wurden erzeugt."
else
  chmod 0600 "$target_env"
fi
