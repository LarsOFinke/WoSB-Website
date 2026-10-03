#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
target_env="${1:?target environment path required}"
target_credentials="${2:?target credentials path required}"
target_environment="${3:-test}"; requested_hostname="${4:-}"; requested_ip="${5:-}"; requested_letsencrypt_email="${6:-}"; backup_controller_website_host="${7:-}"; backup_controller_website_port="${8:-}"
[[ "$target_environment" =~ ^(test|production)$ ]] || die "Invalid target environment: $target_environment"
source "$INFRA_DIR/scripts/lib/env.sh"
export ENV_FILE="$target_env"
install -d -m 0700 "$(dirname "$target_env")"
if [[ ! -f "$target_env" ]]; then
  install -m 0600 "$INFRA_DIR/.env.example" "$target_env"
  set_env_value DEPLOYMENT_ENVIRONMENT "$target_environment"
  if [[ "$target_environment" == production ]]; then
    [[ -n "$requested_hostname" && -n "$requested_letsencrypt_email" ]] \
      || die "Production setup needs a public hostname and LETSENCRYPT_EMAIL."
    initialize_env "$requested_hostname" "$requested_ip" false admin "RBF Command" "$requested_letsencrypt_email"
    install -m 0600 "$INFRA_DIR/first-run-credentials.txt" "$target_credentials"
    echo "[website] Production environment and first-run credentials were generated on the target."
  else
    initialize_env "$requested_hostname" "$requested_ip" false admin "RBF Command"
    install -m 0600 "$INFRA_DIR/first-run-credentials.txt" "$target_credentials"
    echo "[website] New environment file and first-run credentials were generated."
  fi
else
  chmod 0600 "$target_env"
  existing_environment="$(read_env DEPLOYMENT_ENVIRONMENT)"
  if [[ -n "$existing_environment" && "$existing_environment" != "$target_environment" ]]; then
    die "Existing installation is marked as $existing_environment and cannot be repurposed as $target_environment."
  fi
fi
set_env_value DEPLOYMENT_ENVIRONMENT "$target_environment"
[[ -n "$(read_env RBF_LOOPBACK_PORT)" ]] || set_env_value RBF_LOOPBACK_PORT 18080
runtime_hostname="$(read_env APP_HOSTNAME)"
if [[ "$target_environment" == production ]]; then
  set_env_value CORS_ORIGINS "https://${runtime_hostname}"
  set_env_value SESSION_COOKIE_SECURE true
else
  set_env_value CORS_ORIGINS "http://${runtime_hostname}"
  set_env_value SESSION_COOKIE_SECURE false
fi
if [[ -z "$backup_controller_website_host" ]]; then
  backup_controller_website_host="$(read_env BACKUP_CONTROLLER_WEBSITE_HOST)"
fi
if [[ -z "$backup_controller_website_host" && "$target_environment" == production ]]; then
  backup_controller_website_host="$requested_hostname"
fi
if [[ -z "$backup_controller_website_host" ]]; then
  echo "[website] A deployment-specific backup-controller website host is required for $target_environment." >&2
  exit 1
fi
[[ "$backup_controller_website_host" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$ ]] \
  || { echo "[website] Invalid backup-controller website host: $backup_controller_website_host" >&2; exit 1; }
if [[ -z "$backup_controller_website_port" ]]; then
  backup_controller_website_port="$(read_env BACKUP_CONTROLLER_WEBSITE_SSH_PORT)"
fi
backup_controller_website_port="${backup_controller_website_port:-22}"
[[ "$backup_controller_website_port" =~ ^[0-9]+$ ]] \
  && ((backup_controller_website_port >= 1 && backup_controller_website_port <= 65535)) \
  || { echo "[website] Invalid backup-controller website SSH port: $backup_controller_website_port" >&2; exit 1; }
set_env_value BACKUP_CONTROLLER_WEBSITE_HOST "$backup_controller_website_host"
set_env_value BACKUP_CONTROLLER_WEBSITE_SSH_PORT "$backup_controller_website_port"
