#!/usr/bin/env bash
set -Eeuo pipefail

discord_bot_is_ssh_repository_url() {
  [[ "$REPO_URL" =~ ^ssh:// ]] || [[ "$REPO_URL" =~ ^[^/@[:space:]]+@[^/:[:space:]]+:.+ ]]
}

discord_bot_validate_automation_path() {
  local value="$1" label="$2"
  [[ "$value" == /* ]] || die "$label muss ein absoluter Pfad sein."
  [[ "$value" =~ ^/[A-Za-z0-9._/@+-]+$ ]] \
    || die "$label enthält für den nicht-interaktiven Runner nicht unterstützte Zeichen."
}

discord_bot_configure_git_transport() {
  export GIT_TERMINAL_PROMPT=0

  if ! discord_bot_is_ssh_repository_url; then
    if [[ -n "$GIT_SSH_KEY_FILE" || -n "$GIT_KNOWN_HOSTS_FILE" ]]; then
      log "SSH-Schlüsselkonfiguration wird ignoriert, da die Repository-URL kein SSH-Format verwendet."
    fi
    return 0
  fi

  if [[ -z "$GIT_SSH_KEY_FILE" ]]; then
    log "SSH-Repository ohne expliziten Manager-Schlüssel: Git verwendet den root-eigenen Standard-SSH-Kontext."
    log "Für reproduzierbare Installationen RBF_DISCORD_BOT_GIT_SSH_KEY_FILE und RBF_DISCORD_BOT_GIT_KNOWN_HOSTS_FILE konfigurieren."
    return 0
  fi

  discord_bot_validate_automation_path "$GIT_SSH_KEY_FILE" "RBF_DISCORD_BOT_GIT_SSH_KEY_FILE"
  [[ -f "$GIT_SSH_KEY_FILE" && -r "$GIT_SSH_KEY_FILE" ]] \
    || die "Konfigurierter Git-SSH-Private-Key ist nicht lesbar: $GIT_SSH_KEY_FILE"
  [[ "$GIT_SSH_PORT" =~ ^[0-9]+$ ]] && ((GIT_SSH_PORT >= 1 && GIT_SSH_PORT <= 65535)) \
    || die "RBF_DISCORD_BOT_GIT_SSH_PORT ist ungültig."

  if [[ -z "$GIT_KNOWN_HOSTS_FILE" ]]; then
    GIT_KNOWN_HOSTS_FILE="/root/.ssh/known_hosts"
  fi
  discord_bot_validate_automation_path "$GIT_KNOWN_HOSTS_FILE" "RBF_DISCORD_BOT_GIT_KNOWN_HOSTS_FILE"
  [[ -f "$GIT_KNOWN_HOSTS_FILE" && -r "$GIT_KNOWN_HOSTS_FILE" ]] \
    || die "Konfigurierte known_hosts-Datei ist nicht lesbar: $GIT_KNOWN_HOSTS_FILE"

  export GIT_SSH_COMMAND="/usr/bin/ssh -F /dev/null -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$GIT_KNOWN_HOSTS_FILE -o ConnectTimeout=20 -p $GIT_SSH_PORT -i $GIT_SSH_KEY_FILE"
  log "Git-SSH für den Bot-Manager verwendet einen expliziten Schlüssel und eine explizite known_hosts-Datei."
}
