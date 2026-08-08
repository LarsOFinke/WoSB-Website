#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
target_env="${1:?target environment path required}"
target_credentials="${2:?target credentials path required}"
target_environment="${3:-test}"
[[ "$target_environment" =~ ^(test|production)$ ]] || die "Ungültige Zielumgebung: $target_environment"
source "$INFRA_DIR/scripts/lib/env.sh"
export ENV_FILE="$target_env"
install -d -m 0700 "$(dirname "$target_env")"
if [[ ! -f "$target_env" ]]; then
  if [[ "$target_environment" == production ]]; then
    die "Production benötigt eine explizit vorbereitete private Environment-Datei mit TLS_MODE=letsencrypt und LETSENCRYPT_EMAIL."
  fi
  initialize_env "" "" false admin "RBF Command" auto "" true
  install -m 0600 "$INFRA_DIR/first-run-credentials.txt" "$target_credentials"
  echo "[website] Neue Environment-Datei und First-Run-Zugangsdaten wurden erzeugt."
else
  chmod 0600 "$target_env"
fi
set_env_value DEPLOYMENT_ENVIRONMENT "$target_environment"
