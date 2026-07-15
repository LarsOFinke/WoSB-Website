#!/usr/bin/env bash
set -Eeuo pipefail

DISCORD_BOT_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$DISCORD_BOT_LIB_DIR/../.." && pwd)"

source "$INFRA_DIR/scripts/lib/docker.sh"
source "$INFRA_DIR/scripts/lib/json.sh"
source "$INFRA_DIR/scripts/lib/host/control.sh"
source "$DISCORD_BOT_LIB_DIR/context.sh"
source "$DISCORD_BOT_LIB_DIR/git.sh"
source "$DISCORD_BOT_LIB_DIR/service.sh"
source "$DISCORD_BOT_LIB_DIR/request.sh"
source "$DISCORD_BOT_LIB_DIR/status.sh"
source "$DISCORD_BOT_LIB_DIR/configuration.sh"
source "$DISCORD_BOT_LIB_DIR/actions.sh"

DISCORD_BOT_COMPLETE=false
OPERATION=""
REQUESTED_BY=""
REQUESTED_AT=""
STARTED_AT=""
STATUS_ONLY=false

discord_bot_usage() {
  cat <<'USAGE'
Usage: manage-discord-bot.sh [--status-only]

Without options, process the JSON request written by the administrator panel.
USAGE
}

discord_bot_parse_options() {
  case "${1:-}" in
    "") ;;
    --status-only) STATUS_ONLY=true ;;
    -h|--help) discord_bot_usage; exit 0 ;;
    *) die "Unbekannte Discord-Bot-Manager-Option: $1" ;;
  esac
  (($# <= 1)) || die "Zu viele Discord-Bot-Manager-Optionen."
}

discord_bot_on_exit() {
  local code=$?
  rm -f "$REQUEST_FILE"
  if [[ "$DISCORD_BOT_COMPLETE" != true && "$code" -ne 0 && -n "$OPERATION" ]]; then
    discord_bot_status_write \
      failed \
      "$OPERATION" \
      "Discord-Bot-Aktion fehlgeschlagen (Exit $code)." \
      "$REQUESTED_BY" \
      "$REQUESTED_AT" \
      "$STARTED_AT" \
      "$(date --iso-8601=seconds)" || true
  fi
}

discord_bot_run_request() {
  [[ -e "$INBOX_REQUEST_FILE" ]] || die "Keine Discord-Bot-Anforderung im Control-Inbox-Verzeichnis gefunden."
  rm -f "$REQUEST_FILE"
  claim_control_request "$INBOX_REQUEST_FILE" "$REQUEST_FILE" 10001
  discord_bot_load_request
  if ! discord_bot_operation_is_valid "$OPERATION"; then
    discord_bot_status_write \
      failed status "Ungültige Discord-Bot-Aktion." \
      "$REQUESTED_BY" "$REQUESTED_AT" "" "$(date --iso-8601=seconds)"
    rm -f "$REQUEST_FILE"
    die "Ungültige Aktion: $OPERATION"
  fi

  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    discord_bot_status_write \
      failed "$OPERATION" "Eine andere Discord-Bot-Aktion läuft bereits." \
      "$REQUESTED_BY" "$REQUESTED_AT" "" "$(date --iso-8601=seconds)"
    die "Eine andere Discord-Bot-Aktion läuft bereits."
  fi

  STARTED_AT="$(date --iso-8601=seconds)"
  discord_bot_status_write \
    running "$OPERATION" "Discord-Bot-Aktion wird ausgeführt." \
    "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT"
  exec > >(tee -a "$LOG_FILE") 2>&1
  trap discord_bot_on_exit EXIT

  discord_bot_execute_operation

  local finished_at
  finished_at="$(date --iso-8601=seconds)"
  discord_bot_status_write \
    succeeded "$OPERATION" "Discord-Bot-Aktion erfolgreich abgeschlossen." \
    "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT" "$finished_at"
  DISCORD_BOT_COMPLETE=true
}

discord_bot_main() {
  discord_bot_parse_options "$@"
  [[ "$EUID" -eq 0 ]] || die "Discord-Bot-Verwaltung benötigt root-Rechte."
  require_command python3
  require_command systemctl
  require_command flock

  discord_bot_context_init
  if [[ "$STATUS_ONLY" == true ]]; then
    discord_bot_status_write idle status "Discord-Bot-Status aktualisiert."
    return 0
  fi

  discord_bot_run_request
}
