#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"
source "$INFRA_DIR/scripts/lib/env.sh"
source "$INFRA_DIR/scripts/lib/host.sh"
source "$INFRA_DIR/scripts/lib/docker.sh"

PROFILE=full
SKIP_HOST=false
NO_START=false
CONFIGURE_FIREWALL=true
INSTALL_SYSTEMD=true
REGENERATE_SECRETS=false
REQUESTED_HOSTNAME=""
REQUESTED_IP=""
REQUESTED_TLS_MODE=""
REQUESTED_LETSENCRYPT_EMAIL=""
REQUESTED_LETSENCRYPT_STAGING=""
ADMIN_USERNAME=admin
ADMIN_DISPLAY_NAME="RBF Command"

usage() {
  cat <<'USAGE'
Royal Blackwater Fleet - Raspberry Pi First-Run Setup

Usage:
  sudo ./infrastructure/setup.sh [options]

Options:
  --profile core|full       core: app stack, full: app stack + Uptime Kuma (default)
  --domain NAME             Public domain (default: royal-blackwater-fleet.eu)
  --hostname NAME           Compatibility alias for --domain
  --ip ADDRESS              LAN address for certificate and startup summary
  --admin-username NAME     Initial administrator username (default: admin)
  --admin-display-name NAME Initial administrator display name
  --tls-mode MODE           auto, letsencrypt or self-signed (default: auto)
  --letsencrypt-email MAIL  Contact email required for public certificates
  --letsencrypt-staging     Use the Let's Encrypt staging CA for testing
  --skip-host               Skip apt, Docker, firewall and systemd provisioning
  --no-firewall             Do not enable/configure UFW
  --no-systemd              Do not install the boot service
  --no-start                Configure everything but do not start containers
  --regenerate-secrets      Replace PostgreSQL/admin secrets and TLS certificate
  -h, --help                Show this help
USAGE
}

while (($#)); do
  case "$1" in
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --domain|--hostname) REQUESTED_HOSTNAME="${2:-}"; shift 2 ;;
    --ip) REQUESTED_IP="${2:-}"; shift 2 ;;
    --admin-username) ADMIN_USERNAME="${2:-}"; shift 2 ;;
    --admin-display-name) ADMIN_DISPLAY_NAME="${2:-}"; shift 2 ;;
    --tls-mode) REQUESTED_TLS_MODE="${2:-}"; shift 2 ;;
    --letsencrypt-email) REQUESTED_LETSENCRYPT_EMAIL="${2:-}"; shift 2 ;;
    --letsencrypt-staging) REQUESTED_LETSENCRYPT_STAGING=true; shift ;;
    --skip-host) SKIP_HOST=true; shift ;;
    --no-firewall) CONFIGURE_FIREWALL=false; shift ;;
    --no-systemd) INSTALL_SYSTEMD=false; shift ;;
    --no-start) NO_START=true; shift ;;
    --regenerate-secrets) REGENERATE_SECRETS=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unbekannte Option: $1" ;;
  esac
done

[[ "$PROFILE" == core || "$PROFILE" == full ]] || die "--profile muss core oder full sein."
[[ "$ADMIN_USERNAME" =~ ^[A-Za-z0-9_.-]{3,40}$ ]] || die "Ungültiger Admin-Benutzername."

if [[ "$SKIP_HOST" == false && "$EUID" -ne 0 ]]; then
  command -v sudo >/dev/null 2>&1 || die "Bitte als root starten oder --skip-host verwenden."
  sudo_args=(--profile "$PROFILE" --admin-username "$ADMIN_USERNAME" --admin-display-name "$ADMIN_DISPLAY_NAME")
  [[ -n "$REQUESTED_HOSTNAME" ]] && sudo_args+=(--domain "$REQUESTED_HOSTNAME")
  [[ -n "$REQUESTED_TLS_MODE" ]] && sudo_args+=(--tls-mode "$REQUESTED_TLS_MODE")
  [[ -n "$REQUESTED_LETSENCRYPT_EMAIL" ]] && sudo_args+=(--letsencrypt-email "$REQUESTED_LETSENCRYPT_EMAIL")
  [[ "$REQUESTED_LETSENCRYPT_STAGING" == true ]] && sudo_args+=(--letsencrypt-staging)
  [[ -n "$REQUESTED_IP" ]] && sudo_args+=(--ip "$REQUESTED_IP")
  [[ "$CONFIGURE_FIREWALL" == false ]] && sudo_args+=(--no-firewall)
  [[ "$INSTALL_SYSTEMD" == false ]] && sudo_args+=(--no-systemd)
  [[ "$NO_START" == true ]] && sudo_args+=(--no-start)
  [[ "$REGENERATE_SECRETS" == true ]] && sudo_args+=(--regenerate-secrets)
  exec sudo --preserve-env=DEBUG bash "$0" "${sudo_args[@]}"
fi
log "RBF First-Run Setup wird vorbereitet."
log "Profil: $PROFILE | Host-Provisioning: $([[ "$SKIP_HOST" == true ]] && echo aus || echo an)"

migrate_legacy_runtime_names() {
  [[ -f "$ENV_FILE" ]] || return 0
  local legacy_project
  legacy_project="$(read_env COMPOSE_PROJECT_NAME)"
  [[ "$legacy_project" == rbv-hub || "$legacy_project" == blackwater-hub ]] || return 0

  log "Migriere den früheren Docker-Projektnamen ${legacy_project} auf rbf-hub."
  if command -v docker >/dev/null 2>&1 && compose_binary >/dev/null 2>&1; then
    bw_compose_with_profiles down --remove-orphans || warn "Der alte Stack konnte nicht vollständig gestoppt werden; Setup setzt die Migration fort."
  fi
  set_env_value COMPOSE_PROJECT_NAME rbf-hub
}

if [[ "$SKIP_HOST" == false ]]; then
  install_host_dependencies
else
  require_command docker
  compose_binary >/dev/null || die "Docker Compose fehlt."
  require_command openssl
fi

migrate_legacy_runtime_names
initialize_env "$REQUESTED_HOSTNAME" "$REQUESTED_IP" "$REGENERATE_SECRETS" "$ADMIN_USERNAME" "$ADMIN_DISPLAY_NAME" "$REQUESTED_TLS_MODE" "$REQUESTED_LETSENCRYPT_EMAIL" "$REQUESTED_LETSENCRYPT_STAGING"
if [[ "$PROFILE" == full ]]; then
  set_env_value ENABLE_MONITORING true
else
  set_env_value ENABLE_MONITORING false
fi
validate_env

if [[ "$REGENERATE_SECRETS" == true ]]; then
  rm -f "$INFRA_DIR/data/certs/fullchain.pem" "$INFRA_DIR/data/certs/privkey.pem"
fi
prepare_data_directories
generate_self_signed_certificate

if [[ "$SKIP_HOST" == false && "$CONFIGURE_FIREWALL" == true ]]; then
  configure_firewall
fi

if [[ "$SKIP_HOST" == false && "$INSTALL_SYSTEMD" == true ]]; then
  "$INFRA_DIR/scripts/deployment/install-systemd.sh"
fi

bw_compose_with_profiles config >/dev/null
success "Compose-Konfiguration ist gültig."

if [[ "$NO_START" == false ]]; then
  bw_compose_with_profiles pull postgres
  if [[ "$PROFILE" == full ]]; then
    bw_compose_with_profiles pull uptime-kuma
  fi
  bw_compose build api gateway
  deploy_stack
  "$INFRA_DIR/scripts/checks/smoke-test.sh" --insecure
  configure_production_tls
  "$INFRA_DIR/scripts/checks/smoke-test.sh"
else
  warn "Containerstart wurde mit --no-start übersprungen."
fi

app_ip="$(read_env APP_IP)"
app_hostname="$(read_env APP_HOSTNAME)"
cat <<SUMMARY

============================================================
 Royal Blackwater Fleet ist eingerichtet
============================================================
 Fleet Hub:       https://${app_hostname}
 LAN fallback:    https://${app_ip}
 API readiness:  https://${app_hostname}/api/health/ready
 PostgreSQL:      localhost:$(read_env POSTGRES_LOCAL_PORT) (nur Loopback)
 Monitoring:      $([[ "$PROFILE" == full ]] && printf 'https://%s:%s' "${app_hostname}" "$(read_env MONITORING_HTTPS_PORT)" || printf 'deaktiviert')
 TLS provider:    $(read_env CERTIFICATE_PROVIDER)
 Credentials:     $INFRA_DIR/first-run-credentials.txt

 Für Let's Encrypt müssen DNS sowie TCP-Port 80 und 443 auf diesen Pi zeigen.
 Ohne erfolgreiche Domainvalidierung bleibt das Bootstrap-Zertifikat aktiv.
============================================================
SUMMARY
