#!/usr/bin/env bash
set -Eeuo pipefail

discord_bot_install() {
  [[ -n "$REPO_URL" ]] || die "RBF_DISCORD_BOT_REPO_URL ist nicht in $MANAGER_ENV konfiguriert."
  require_command git
  discord_bot_configure_git_transport

  if [[ ! -d "$INSTALL_DIR/.git" ]]; then
    [[ ! -e "$INSTALL_DIR" || -z "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]] \
      || die "Installationsverzeichnis ist nicht leer: $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    log "Bot-Repository wird direkt geklont; es wird kein separater git-ls-remote-Preflight verwendet."
    git clone --branch "$BRANCH" --single-branch -- "$REPO_URL" "$INSTALL_DIR"
  else
    log "Vorhandener Git-Checkout wird für die Installation verwendet: $INSTALL_DIR"
  fi

  /usr/bin/env bash "$INSTALL_DIR/scripts/install.sh"
  discord_bot_gateway_access --configure-only
}

discord_bot_configure() {
  local restart_after_configuration
  restart_after_configuration="$(discord_bot_apply_configuration)"
  discord_bot_gateway_access --configure-only

  if [[ "$restart_after_configuration" == true ]]; then
    systemctl restart "$SERVICE_NAME"
    discord_bot_gateway_access --check-only
  fi
}

discord_bot_update() {
  [[ -x "$INSTALL_DIR/scripts/update.sh" ]] || die "Bot-Update-Skript fehlt."
  require_command git
  discord_bot_configure_git_transport
  discord_bot_gateway_access --configure-only
  /usr/bin/env bash "$INSTALL_DIR/scripts/update.sh"
  discord_bot_gateway_access --check-only
}

discord_bot_start_or_restart() {
  local operation="$1"
  discord_bot_gateway_access --configure-only
  systemctl "$operation" "$SERVICE_NAME"
  discord_bot_gateway_access --check-only
}

discord_bot_execute_operation() {
  case "$OPERATION" in
    refresh)
      log "Discord-Bot-Hoststatus wird aktualisiert."
      if discord_bot_is_installed && [[ "$(discord_bot_service_state)" == active ]]; then
        discord_bot_gateway_access
      fi
      ;;
    install) discord_bot_install ;;
    configure) discord_bot_configure ;;
    update) discord_bot_update ;;
    start|restart) discord_bot_start_or_restart "$OPERATION" ;;
    stop) systemctl stop "$SERVICE_NAME" ;;
  esac
}
