#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"

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
CONFIG_DIR="/etc/rbf-discord-bot"
BOT_ENV_FILE="$CONFIG_DIR/bot.env"
BOT_CONFIG_FILE="$CONFIG_DIR/bot.yaml"
CONFIG_SUMMARY_FILE="$CONFIG_DIR/config-summary.json"
STATUS_ONLY=false
[[ "${1:-}" == "--status-only" ]] && STATUS_ONLY=true

[[ -f "$MANAGER_ENV" ]] && source "$MANAGER_ENV"
REPO_URL="${RBF_DISCORD_BOT_REPO_URL:-}"
BRANCH="${RBF_DISCORD_BOT_BRANCH:-main}"
INSTALL_DIR="${RBF_DISCORD_BOT_INSTALL_DIR:-/opt/rbf-discord-bot}"
GIT_SSH_KEY_FILE="${RBF_DISCORD_BOT_GIT_SSH_KEY_FILE:-}"
GIT_KNOWN_HOSTS_FILE="${RBF_DISCORD_BOT_GIT_KNOWN_HOSTS_FILE:-}"
GIT_SSH_PORT="${RBF_DISCORD_BOT_GIT_SSH_PORT:-22}"
BIND_HOST="${RBF_DISCORD_BOT_BIND_HOST:-0.0.0.0}"
BOT_PORT=8765
FIREWALL_MODE="${RBF_DISCORD_BOT_FIREWALL_MODE:-auto}"
GATEWAY_ACCESS_SCRIPT="$INFRA_DIR/scripts/services/configure-discord-bot-gateway.sh"
SERVICE_NAME="rbf-discord-bot.service"

mkdir -p "$CONTROL_DIR"
touch "$LOG_FILE"
chmod 664 "$LOG_FILE"

is_ssh_repository_url() {
  [[ "$REPO_URL" =~ ^ssh:// ]] || [[ "$REPO_URL" =~ ^[^/@[:space:]]+@[^/:[:space:]]+:.+ ]]
}

validate_automation_path() {
  local value="$1" label="$2"
  [[ "$value" == /* ]] || die "$label muss ein absoluter Pfad sein."
  [[ "$value" =~ ^/[A-Za-z0-9._/@+-]+$ ]] || die "$label enthält für den nicht-interaktiven Runner nicht unterstützte Zeichen."
}

configure_git_transport() {
  export GIT_TERMINAL_PROMPT=0

  if ! is_ssh_repository_url; then
    [[ -z "$GIT_SSH_KEY_FILE" && -z "$GIT_KNOWN_HOSTS_FILE" ]] || log "SSH-Schlüsselkonfiguration wird ignoriert, da die Repository-URL kein SSH-Format verwendet."
    return
  fi

  if [[ -z "$GIT_SSH_KEY_FILE" ]]; then
    log "SSH-Repository ohne expliziten Manager-Schlüssel: Git verwendet den root-eigenen Standard-SSH-Kontext."
    log "Für reproduzierbare Installationen RBF_DISCORD_BOT_GIT_SSH_KEY_FILE und RBF_DISCORD_BOT_GIT_KNOWN_HOSTS_FILE konfigurieren."
    return
  fi

  validate_automation_path "$GIT_SSH_KEY_FILE" "RBF_DISCORD_BOT_GIT_SSH_KEY_FILE"
  [[ -f "$GIT_SSH_KEY_FILE" && -r "$GIT_SSH_KEY_FILE" ]] || die "Konfigurierter Git-SSH-Private-Key ist nicht lesbar: $GIT_SSH_KEY_FILE"
  [[ "$GIT_SSH_PORT" =~ ^[0-9]+$ ]] && (( GIT_SSH_PORT >= 1 && GIT_SSH_PORT <= 65535 )) || die "RBF_DISCORD_BOT_GIT_SSH_PORT ist ungültig."

  if [[ -z "$GIT_KNOWN_HOSTS_FILE" ]]; then
    GIT_KNOWN_HOSTS_FILE="/root/.ssh/known_hosts"
  fi
  validate_automation_path "$GIT_KNOWN_HOSTS_FILE" "RBF_DISCORD_BOT_GIT_KNOWN_HOSTS_FILE"
  [[ -f "$GIT_KNOWN_HOSTS_FILE" && -r "$GIT_KNOWN_HOSTS_FILE" ]] || die "Konfigurierte known_hosts-Datei ist nicht lesbar: $GIT_KNOWN_HOSTS_FILE"

  export GIT_SSH_COMMAND="/usr/bin/ssh -F /dev/null -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$GIT_KNOWN_HOSTS_FILE -o ConnectTimeout=20 -p $GIT_SSH_PORT -i $GIT_SSH_KEY_FILE"
  log "Git-SSH für den Bot-Manager verwendet einen expliziten Schlüssel und eine explizite known_hosts-Datei."
}

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
  STATE="$state" OPERATION="$operation" MESSAGE="$message" REQUESTED_BY="$requested_by" REQUESTED_AT="$requested_at" STARTED_AT="$started_at" FINISHED_AT="$finished_at" CONFIGURED="$([[ -n "$REPO_URL" ]] && echo true || echo false)" INSTALLED="$(installed && echo true || echo false)" SERVICE_STATE="$(service_state)" VERSION_VALUE="$(version_value)" COMMIT_VALUE="$(commit_value)" STATUS_FILE="$STATUS_FILE" CONFIG_SUMMARY_FILE="$CONFIG_SUMMARY_FILE" python3 <<'PY'
import json, os
from pathlib import Path

path = Path(os.environ['STATUS_FILE'])
summary_path = Path(os.environ['CONFIG_SUMMARY_FILE'])
configuration = {}
if summary_path.is_file():
    try:
        loaded = json.loads(summary_path.read_text(encoding='utf-8'))
        if isinstance(loaded, dict):
            configuration = loaded
    except (OSError, json.JSONDecodeError):
        configuration = {'valid': False, 'message': 'Configuration summary could not be read.'}

payload = {
  'state': os.environ['STATE'], 'operation': os.environ['OPERATION'], 'message': os.environ['MESSAGE'],
  'configured': os.environ['CONFIGURED'] == 'true', 'installed': os.environ['INSTALLED'] == 'true',
  'service_state': os.environ['SERVICE_STATE'] or 'unknown', 'version': os.environ['VERSION_VALUE'] or None,
  'commit': os.environ['COMMIT_VALUE'] or None, 'requested_by': os.environ['REQUESTED_BY'] or None,
  'requested_at': os.environ['REQUESTED_AT'] or None, 'started_at': os.environ['STARTED_AT'] or None,
  'finished_at': os.environ['FINISHED_AT'] or None, 'configuration': configuration,
}
tmp = path.with_name('.' + path.name + '.tmp')
tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tmp.replace(path)
path.chmod(0o664)
PY
}

apply_configuration() {
  [[ -x "$INSTALL_DIR/.venv/bin/python" ]] || die "Bot-Python-Umgebung fehlt. Zuerst den Bot installieren."
  local service_group="root"
  getent group rbf-discord >/dev/null 2>&1 && service_group="rbf-discord"
  install -d -m 0750 -o root -g "$service_group" "$CONFIG_DIR" || return 1
  RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
    "$INSTALL_DIR/.venv/bin/python" - "$REQUEST_FILE" "$INSTALL_DIR" "$BOT_ENV_FILE" "$BOT_CONFIG_FILE" "$CONFIG_SUMMARY_FILE" <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
import grp
import json
import os
from pathlib import Path
import secrets
import sys
from urllib.parse import urlsplit

import yaml
from rbf_discord_bot.config import BotConfig

request_path, install_dir, env_path, config_path, summary_path = map(Path, sys.argv[1:])
payload = json.loads(request_path.read_text(encoding='utf-8'))
configuration = payload.get('configuration')
if not isinstance(configuration, dict):
    raise SystemExit('Missing Discord bot configuration payload.')


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def valid_secret(value: str, minimum: int) -> bool:
    return len(value) >= minimum and not value.startswith('CHANGE_ME') and '#' not in value and not any(character.isspace() for character in value)


def atomic_write(path: Path, content: str, *, mode: int = 0o640) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.tmp')
    temporary.write_text(content, encoding='utf-8')
    os.chmod(temporary, mode)
    try:
        group_id = grp.getgrnam('rbf-discord').gr_gid
        os.chown(temporary, 0, group_id)
    except KeyError:
        pass
    os.replace(temporary, path)
    os.chmod(path, mode)

existing_env = parse_env(env_path)
discord_token = str(configuration.get('discord_bot_token') or existing_env.get('DISCORD_BOT_TOKEN') or '').strip()
webhook_secret = str(configuration.get('webhook_secret') or existing_env.get('RBF_WEBHOOK_SECRET') or '').strip()
management_token = str(existing_env.get('BOT_MANAGEMENT_TOKEN') or '').strip()
if not valid_secret(discord_token, 20):
    raise SystemExit('A valid Discord bot token is required.')
if not valid_secret(webhook_secret, 32):
    raise SystemExit('A webhook signing secret with at least 32 characters is required.')
if not valid_secret(management_token, 32):
    management_token = secrets.token_urlsafe(48)

website_base_url = str(configuration.get('website_base_url') or '').strip().rstrip('/')
parsed_url = urlsplit(website_base_url)
if parsed_url.scheme != 'https' or not parsed_url.hostname or parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment or parsed_url.path not in {'', '/'}:
    raise SystemExit('The website base URL must be an absolute HTTPS URL without credentials, query or fragment.')

channels = configuration.get('channels')
if not isinstance(channels, dict):
    raise SystemExit('Channel mappings are required.')
clean_channels: dict[str, str] = {}
for raw_key, raw_channel_id in channels.items():
    key = str(raw_key).strip().lower()
    channel_id = str(raw_channel_id).strip()
    if not key or not key[0].isalpha() or any(character not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for character in key):
        raise SystemExit(f'Invalid channel key: {key!r}')
    if not channel_id.isdigit() or not 15 <= len(channel_id) <= 22:
        raise SystemExit(f'Invalid Discord channel ID for {key!r}.')
    clean_channels[key] = channel_id
required_channels = {'events', 'guides', 'builds', 'forum', 'default'}
missing_channels = sorted(required_channels - set(clean_channels))
if missing_channels:
    raise SystemExit('Missing channel mappings: ' + ', '.join(missing_channels))

example_path = install_dir / 'config' / 'bot.yaml.example'
source_path = config_path if config_path.is_file() else example_path
raw_config = yaml.safe_load(source_path.read_text(encoding='utf-8')) or {}
raw_config.setdefault('server', {})
raw_config['server']['host'] = os.environ['RBF_DISCORD_BOT_BIND_HOST']
raw_config['server']['port'] = 8765
raw_config['server']['public_webhook_path'] = '/webhooks/rbf'
raw_config.setdefault('security', {})
raw_config['security']['timestamp_tolerance_seconds'] = int(configuration.get('timestamp_tolerance_seconds', 300))
raw_config['security']['management_token_header'] = 'X-RBF-Bot-Token'
raw_config['website'] = {'base_url': website_base_url}
raw_config['channels'] = clean_channels
raw_config.setdefault('discord', {})
raw_config['discord']['api_base_url'] = 'https://discord.com/api/v10'
raw_config['discord']['request_timeout_seconds'] = float(configuration.get('request_timeout_seconds', 15))
raw_config['discord']['max_attempts'] = int(configuration.get('max_attempts', 3))
raw_config['discord']['suppress_notifications'] = bool(configuration.get('suppress_notifications', False))
validated = BotConfig.model_validate(raw_config)

config_content = yaml.safe_dump(validated.model_dump(mode='json'), sort_keys=False, allow_unicode=True)
env_content = '\n'.join([
    '# Managed through the Royal Blackwater Fleet administrator panel.',
    'DISCORD_BOT_TOKEN=' + discord_token,
    'RBF_WEBHOOK_SECRET=' + webhook_secret,
    'BOT_MANAGEMENT_TOKEN=' + management_token,
    'RBF_BOT_CONFIG=/etc/rbf-discord-bot/bot.yaml',
    'RBF_BOT_DATA_DIR=/var/lib/rbf-discord-bot',
    'RBF_BOT_LOG_LEVEL=INFO',
    '',
])
atomic_write(env_path, env_content)
atomic_write(config_path, config_content)

summary = {
    'ready': True,
    'env_file_present': True,
    'config_file_present': True,
    'discord_token_configured': True,
    'webhook_secret_configured': True,
    'management_token_configured': True,
    'website_base_url': website_base_url,
    'channels': clean_channels,
    'suppress_notifications': validated.discord.suppress_notifications,
    'timestamp_tolerance_seconds': validated.security.timestamp_tolerance_seconds,
    'request_timeout_seconds': validated.discord.request_timeout_seconds,
    'max_attempts': validated.discord.max_attempts,
    'bind_host': validated.server.host,
    'listen_port': validated.server.port,
    'firewall_mode': os.environ['RBF_DISCORD_BOT_FIREWALL_MODE'],
    'public_webhook_path': validated.server.public_webhook_path,
    'updated_at': datetime.now(timezone.utc).isoformat(),
    'valid': True,
    'message': 'Configuration validated and written by the host runner.',
}
atomic_write(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print('true' if bool(configuration.get('restart_after_save', True)) else 'false')
PY
}

if [[ "$STATUS_ONLY" == true ]]; then
  status_write idle status "Discord-Bot-Status aktualisiert."
  exit 0
fi

OPERATION="$(read_request_value operation)"
REQUESTED_BY="$(read_request_value requested_by)"
REQUESTED_AT="$(read_request_value requested_at)"
case "$OPERATION" in refresh|install|update|start|stop|restart|configure) ;; *) status_write failed status "Ungültige Discord-Bot-Aktion." "$REQUESTED_BY" "$REQUESTED_AT" "" "$(date --iso-8601=seconds)"; rm -f "$REQUEST_FILE"; die "Ungültige Aktion: $OPERATION" ;; esac

exec 9>"$LOCK_FILE"
flock -n 9 || die "Eine andere Discord-Bot-Aktion läuft bereits."
STARTED_AT="$(date --iso-8601=seconds)"
status_write running "$OPERATION" "Discord-Bot-Aktion wird ausgeführt." "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT"
exec > >(tee -a "$LOG_FILE") 2>&1

complete=false
on_exit() {
  code=$?
  rm -f "$REQUEST_FILE"
  if [[ "$complete" != true && "$code" -ne 0 ]]; then
    status_write failed "$OPERATION" "Discord-Bot-Aktion fehlgeschlagen (Exit $code)." "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT" "$(date --iso-8601=seconds)" || true
  fi
}
trap on_exit EXIT

case "$OPERATION" in
  refresh)
    log "Discord-Bot-Hoststatus wird aktualisiert."
    if installed && [[ "$(service_state)" == active ]]; then
      RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
        /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT"
    fi
    ;;
  install)
    [[ -n "$REPO_URL" ]] || die "RBF_DISCORD_BOT_REPO_URL ist nicht in $MANAGER_ENV konfiguriert."
    require_command git
    configure_git_transport
    if [[ ! -d "$INSTALL_DIR/.git" ]]; then
      [[ ! -e "$INSTALL_DIR" || -z "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]] || die "Installationsverzeichnis ist nicht leer: $INSTALL_DIR"
      rm -rf "$INSTALL_DIR"
      log "Bot-Repository wird direkt geklont; es wird kein separater git-ls-remote-Preflight verwendet."
      git clone --branch "$BRANCH" --single-branch -- "$REPO_URL" "$INSTALL_DIR"
    else
      log "Vorhandener Git-Checkout wird für die Installation verwendet: $INSTALL_DIR"
    fi
    /usr/bin/env bash "$INSTALL_DIR/scripts/install.sh"
    RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
      /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" --configure-only
    ;;
  configure)
    RESTART_AFTER_CONFIGURATION="$(apply_configuration)"
    RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
      /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" --configure-only
    if [[ "$RESTART_AFTER_CONFIGURATION" == "true" ]]; then
      systemctl restart "$SERVICE_NAME"
      RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
        /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" --check-only
    fi
    ;;
  update)
    [[ -x "$INSTALL_DIR/scripts/update.sh" ]] || die "Bot-Update-Skript fehlt."
    require_command git
    configure_git_transport
    RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
      /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" --configure-only
    /usr/bin/env bash "$INSTALL_DIR/scripts/update.sh"
    RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
      /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" --check-only
    ;;
  start|restart)
    RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
      /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" --configure-only
    systemctl "$OPERATION" "$SERVICE_NAME"
    RBF_DISCORD_BOT_BIND_HOST="$BIND_HOST" RBF_DISCORD_BOT_FIREWALL_MODE="$FIREWALL_MODE" \
      /usr/bin/env bash "$GATEWAY_ACCESS_SCRIPT" --check-only
    ;;
  stop)
    systemctl stop "$SERVICE_NAME"
    ;;
esac

FINISHED_AT="$(date --iso-8601=seconds)"
status_write succeeded "$OPERATION" "Discord-Bot-Aktion erfolgreich abgeschlossen." "$REQUESTED_BY" "$REQUESTED_AT" "$STARTED_AT" "$FINISHED_AT"
complete=true
