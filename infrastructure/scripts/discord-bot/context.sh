#!/usr/bin/env bash
set -Eeuo pipefail

discord_bot_context_init() {
  CONTROL_ROOT="$INFRA_DIR/data/control"
  INBOX_DIR="$CONTROL_ROOT/inbox"
  STATUS_DIR="$CONTROL_ROOT/status"
  RUN_DIR="$CONTROL_ROOT/run"
  INBOX_REQUEST_FILE="$INBOX_DIR/discord-bot.request"
  REQUEST_FILE="$RUN_DIR/discord-bot.request.$$"
  STATUS_FILE="$STATUS_DIR/discord-bot-status.json"
  LOG_FILE="$STATUS_DIR/discord-bot.log"
  LOCK_FILE="$RUN_DIR/discord-bot.lock"
  MANAGER_ENV="/etc/rbf-hub/discord-bot-manager.env"
  CONFIG_DIR="/etc/rbf-discord-bot"
  BOT_ENV_FILE="$CONFIG_DIR/bot.env"
  BOT_CONFIG_FILE="$CONFIG_DIR/bot.yaml"
  CONFIG_SUMMARY_FILE="$CONFIG_DIR/config-summary.json"
  SERVICE_NAME="rbf-discord-bot.service"
  BOT_PORT=8765
  GATEWAY_ACCESS_SCRIPT="$INFRA_DIR/scripts/services/configure-discord-bot-gateway.sh"
  CONFIGURATION_SCRIPT="$INFRA_DIR/scripts/discord-bot/apply-configuration.py"

  [[ -f "$MANAGER_ENV" ]] && source "$MANAGER_ENV"
  REPO_URL="${RBF_DISCORD_BOT_REPO_URL:-}"
  BRANCH="${RBF_DISCORD_BOT_BRANCH:-main}"
  INSTALL_DIR="${RBF_DISCORD_BOT_INSTALL_DIR:-/opt/rbf-discord-bot}"
  GIT_SSH_KEY_FILE="${RBF_DISCORD_BOT_GIT_SSH_KEY_FILE:-}"
  GIT_KNOWN_HOSTS_FILE="${RBF_DISCORD_BOT_GIT_KNOWN_HOSTS_FILE:-}"
  GIT_SSH_PORT="${RBF_DISCORD_BOT_GIT_SSH_PORT:-22}"
  BIND_HOST="${RBF_DISCORD_BOT_BIND_HOST:-0.0.0.0}"
  FIREWALL_MODE="${RBF_DISCORD_BOT_FIREWALL_MODE:-auto}"

  mkdir -p "$INBOX_DIR" "$STATUS_DIR" "$RUN_DIR"
  chown 10001:10001 "$INBOX_DIR"
  chown root:root "$STATUS_DIR" "$RUN_DIR"
  chmod 700 "$INBOX_DIR" "$RUN_DIR"
  chmod 755 "$STATUS_DIR"
  touch "$LOG_FILE"
  chown root:root "$LOG_FILE"
  chmod 644 "$LOG_FILE"
}
