#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "Discord-Bot-Verwaltung benötigt root-Rechte."
require_command python3
require_command systemctl
require_command flock

CONTROL_DIR="$INFRA_DIR/data/control"
REQUEST_FILE="$CONTROL_DIR/discord-bot.request"
STATUS_FILE="$CONTROL_DIR/discord-bot-status.json"
LOG_FILE="$CONTROL_DIR/discord-bot.log"
LOCK_FILE="$CONTROL_DIR/discord-bot.lock"
MANAGER_ENV="/etc/rbf-hub/discord-bot-manager.env"
STATUS_ONLY=false
[[ "${1:-}" == "--status-only" ]] && STATUS_ONLY=true

[[ -f "$MANAGER_ENV" ]] && source "$MANAGER_ENV"
REPO_URL="${RBF_DISCORD_BOT_REPO_URL:-}"
BRANCH="${RBF_DISCORD_BOT_BRANCH:-main}"
INSTALL_DIR="${RBF_DISCORD_BOT_INSTALL_DIR:-/opt/rbf-discord-bot}"
SERVICE_NAME="rbf-discord-bot.service"

mkdir -p "$CONTROL_DIR"
touch "$LOG_FILE"
chmod 664 "$LOG_FILE"

read_request_value() {
  local key="$1"
  python3 - "$REQUEST_FILE" "$key" <<'PY' 2>/dev/null || true
import json, sys
from pathlib import Path
path, key = Path(sys.argv[1]), sys.argv[2]
if path.is_file():
    try:
        print(json.loads(path.read_text(encoding="utf-8")).get(key, "") or "")
    except Exception:
        pass
PY
}

service_state() {
  if ! systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
    printf 'not_installed'
    return
  fi
  systemctl is-active "$SERVICE_NAME" 2>/dev/null || true
}

installed() {
  [[ -x "$INSTALL_DIR/.venv/bin/uvicorn" && -f "/etc/systemd/system/$SERVICE_NAME" ]]
}

version_value() {
  [[ -f "$INSTALL_DIR/VERSION" ]] && tr -d '\r\n' < "$INSTALL_DIR/VERSION" || true
}

commit_value() {
  [[ -d "$INSTALL_DIR/.git" ]] && git -c safe.directory="$INSTALL_DIR" -C "$INSTALL_DIR" rev-parse --short HEAD 2>/dev/null || true
}

status_write() {
  local state="$1" operation="$2" message="$3" requested_by="${4:-}" requested_at="${5:-}" started_at="${6:-}" finished_at="${7:-}"
  STATE="$state" OPERATION="$operation" MESSAGE="$message" REQUESTED_BY="$requested_by" REQUESTED_AT="$requested_at" STARTED_AT="$started_at" FINISHED_AT="$finished_at" CONFIGURED="$([[ -n "$REPO_URL" ]] && echo true || echo false)" INSTALLED="$(installed && echo true || echo false)" SERVICE_STATE="$(service_state)" VERSION_VALUE="$(version_value)" COMMIT_VALUE="$(commit_value)" STATUS_FILE="$STATUS_FILE" python3 <<'PY'
import json, os
from pathlib import Path
path = Path(os.environ['STATUS_FILE'])
payload = {
  'state': os.environ['STATE'], 'operation': os.environ['OPERATION'], 'message': os.environ['MESSAGE'],
  'configured': os.environ['CONFIGURED'] == 'true', 'installed': os.environ['INSTALLED'] == 'true',
  'service_state': os.environ['SERVICE_STATE'] or 'unknown', 'version': os.environ['VERSION_VALUE'] or None,
  'commit': os.environ['COMMIT_VALUE'] or None, 'requested_by': os.environ['REQUESTED_BY'] or None,
  'requested_at': os.environ['REQUESTED_AT'] or None, 'started_at': os.environ['STARTED_AT'] or None,
  'finished_at': os.environ['FINISHED_AT'] or None,
}
tmp = path.with_name('.' + path.name + '.tmp')
tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tmp.replace(path)
path.chmod(0o664)
PY
}

if [[ "$STATUS_ONLY" == true ]]; then
  status_write idle status "Discord-Bot-Status aktualisiert."
  exit 0
fi

OPERATION="$(read_request_value operation)"
REQUESTED_BY="$(read_request_value requested_by)"
REQUESTED_AT="$(read_request_value requested_at)"
rm -f "$REQUEST_FILE"
case "$OPERATION" in refresh|install|update|start|stop|restart) ;; *) status_write failed status "Ungültige Discord-Bot-Aktion." "$REQUESTED_BY" "$REQUESTED_AT" "" "$(date --iso-8601=seconds)"; die "Ungültige Aktion: $OPERATION" ;; esac

exec 9>"$LOCK_FILE"
flock -n 9 || die "Eine andere Discord-Bot-Aktion läuft bereits."
STARTED_AT="$(date --iso-8601=seconds)"
status_write running "$OPERATION" "Discord-Bot-Aktion wird ausgeführt." "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT"
exec > >(tee -a "$LOG_FILE") 2>&1

complete=false
on_exit() {
  code=$?
  if [[ "$complete" != true && "$code" -ne 0 ]]; then
    status_write failed "$OPERATION" "Discord-Bot-Aktion fehlgeschlagen (Exit $code)." "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT" "$(date --iso-8601=seconds)" || true
  fi
}
trap on_exit EXIT

case "$OPERATION" in
  refresh)
    log "Discord-Bot-Hoststatus wird aktualisiert."
    ;;
  install)
    [[ -n "$REPO_URL" ]] || die "RBF_DISCORD_BOT_REPO_URL ist nicht in $MANAGER_ENV konfiguriert."
    require_command git
    if [[ ! -d "$INSTALL_DIR/.git" ]]; then
      [[ ! -e "$INSTALL_DIR" || -z "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]] || die "Installationsverzeichnis ist nicht leer: $INSTALL_DIR"
      rm -rf "$INSTALL_DIR"
      git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$INSTALL_DIR"
    fi
    /usr/bin/env bash "$INSTALL_DIR/scripts/install.sh"
    ;;
  update)
    [[ -x "$INSTALL_DIR/scripts/update.sh" ]] || die "Bot-Update-Skript fehlt."
    /usr/bin/env bash "$INSTALL_DIR/scripts/update.sh"
    ;;
  start|stop|restart)
    systemctl "$OPERATION" "$SERVICE_NAME"
    ;;
esac

FINISHED_AT="$(date --iso-8601=seconds)"
status_write succeeded "$OPERATION" "Discord-Bot-Aktion erfolgreich abgeschlossen." "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT" "$FINISHED_AT"
complete=true
