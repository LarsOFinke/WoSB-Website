#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO_ROOT="$(cd "$INFRA_DIR/.." && pwd)"
ENV_FILE="$INFRA_DIR/.env"
COMPOSE_FILE="${RBF_COMPOSE_FILE:-$INFRA_DIR/compose.yml}"
[[ -f "$COMPOSE_FILE" ]] || COMPOSE_FILE="$INFRA_DIR/compose.release.yml"
RELEASE_ENV_FILE="$INFRA_DIR/.release.env"
ACME_WEBROOT="$INFRA_DIR/data/acme"
CERTBOT_CONFIG_DIR="$INFRA_DIR/data/letsencrypt/config"
CERTBOT_WORK_DIR="$INFRA_DIR/data/letsencrypt/work"
CERTBOT_LOGS_DIR="$INFRA_DIR/data/letsencrypt/logs"

if [[ -t 1 ]]; then
  C_RESET='\033[0m'; C_BLUE='\033[0;34m'; C_GREEN='\033[0;32m'; C_YELLOW='\033[0;33m'; C_RED='\033[0;31m'
else
  C_RESET=''; C_BLUE=''; C_GREEN=''; C_YELLOW=''; C_RED=''
fi

log() { printf '%b[rbf]%b %s\n' "$C_BLUE" "$C_RESET" "$*"; }
success() { printf '%b[ok]%b %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '%b[warn]%b %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
die() { printf '%b[error]%b %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Benötigtes Kommando fehlt: $1"
}

ensure_env_file() {
  [[ -f "$ENV_FILE" ]] || die "Fehlende Konfiguration: $ENV_FILE. Zuerst den Repository-Einstiegspunkt ./setup.sh ausführen."
}

read_env() {
  local key="$1"
  awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); gsub(/^\047|\047$/, ""); gsub(/^\"|\"$/, ""); print; exit}' "$ENV_FILE"
}

# Docker Compose applies the release-specific environment after the shared
# environment. Runtime helpers that need image or project names must use the
# same precedence instead of reading only .env.
read_effective_env() {
  local key="$1" value=""
  if [[ -f "$RELEASE_ENV_FILE" ]]; then
    value="$(awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); gsub(/^\047|\047$/, ""); gsub(/^\"|\"$/, ""); print; exit}' "$RELEASE_ENV_FILE")"
  fi
  [[ -n "$value" ]] || value="$(read_env "$key")"
  printf '%s' "$value"
}

is_true() {
  case "${1,,}" in true|1|yes|on) return 0 ;; *) return 1 ;; esac
}
