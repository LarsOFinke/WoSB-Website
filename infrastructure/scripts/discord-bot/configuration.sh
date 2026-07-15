#!/usr/bin/env bash
set -Eeuo pipefail

discord_bot_apply_configuration() {
  [[ -x "$INSTALL_DIR/.venv/bin/python" ]] || die "Bot-Python-Umgebung fehlt. Zuerst den Bot installieren."

  local service_group=root
  getent group rbf-discord >/dev/null 2>&1 && service_group=rbf-discord
  install -d -m 0750 -o root -g "$service_group" "$CONFIG_DIR"

  RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" \
  RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
  RBF_DISCORD_BOT_PORT="$BOT_PORT" \
    "$INSTALL_DIR/.venv/bin/python" "$CONFIGURATION_SCRIPT" \
      "$REQUEST_FILE" \
      "$INSTALL_DIR" \
      "$BOT_ENV_FILE" \
      "$BOT_CONFIG_FILE" \
      "$CONFIG_SUMMARY_FILE"
}
