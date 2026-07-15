#!/usr/bin/env bash
set -Eeuo pipefail

discord_bot_service_state() {
  if ! systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
    printf 'not_installed'
    return 0
  fi
  systemctl is-active "$SERVICE_NAME" 2>/dev/null || true
}

discord_bot_is_installed() {
  [[ -x "$INSTALL_DIR/.venv/bin/uvicorn" && -f "/etc/systemd/system/$SERVICE_NAME" ]]
}

discord_bot_version() {
  [[ -f "$INSTALL_DIR/VERSION" ]] && tr -d '\r\n' < "$INSTALL_DIR/VERSION" || true
}

discord_bot_commit() {
  [[ -d "$INSTALL_DIR/.git" ]] \
    && git -c safe.directory="$INSTALL_DIR" -C "$INSTALL_DIR" rev-parse --short HEAD 2>/dev/null \
    || true
}

discord_bot_gateway_access() {
  RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" \
  RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
    /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" "$@"
}
