#!/usr/bin/env bash
set -Eeuo pipefail

setup_options_reset() {
  PROFILE=full
  SKIP_HOST=false
  NO_START=false
  CONFIGURE_FIREWALL=true
  INSTALL_SYSTEMD=true
  REGENERATE_SECRETS=false
  VERIFY_BOOTSTRAP_LOGIN=false
  REQUESTED_HOSTNAME=""
  REQUESTED_IP=""
  REQUESTED_TLS_MODE=""
  REQUESTED_LETSENCRYPT_EMAIL=""
  REQUESTED_LETSENCRYPT_STAGING=""
  ADMIN_USERNAME=admin
  ADMIN_DISPLAY_NAME="RBF Command"
  SSH_ADMIN_USERNAME=rbfadmin
  SSH_ADMIN_PUBLIC_KEY_FILE=""
}

setup_usage() {
  cat <<'USAGE'
Royal Blackwater Fleet - Raspberry Pi First-Run Setup

Usage:
  sudo ./infrastructure/setup.sh [options]

The public production and first-run entry point is
./deploy.sh --configure. This setup remains an internal source-tree runner.

Options:
  --profile core|full       core: app stack, full: app stack + Uptime Kuma (default)
  --domain NAME             Public domain (default: royal-blackwater-fleet.eu)
  --hostname NAME           Compatibility alias for --domain
  --ip ADDRESS              LAN address for certificate and startup summary
  --admin-username NAME     Initial administrator username (default: admin)
  --admin-display-name NAME Initial administrator display name
  --ssh-admin-username NAME
                           Host account for key-only SSH administration (default: rbfadmin)
  --ssh-admin-public-key-file PATH
                           External OpenSSH public-key file; repository paths are rejected
  --tls-mode MODE           auto, letsencrypt or self-signed (default: auto)
  --letsencrypt-email MAIL  Contact email required for public certificates
  --letsencrypt-staging     Use the Let's Encrypt staging CA for testing
  --skip-host               Skip apt, Docker, firewall and systemd provisioning
  --no-firewall             Do not enable/configure UFW
  --no-systemd              Do not install the boot service
  --no-start                Configure everything but do not start containers
  --regenerate-secrets      Regenerate bootstrap secrets on an uninitialized installation
  -h, --help                Show this help
USAGE
}

setup_require_option_value() {
  local option="$1" value="${2:-}"
  [[ -n "$value" ]] || die "$option requires a value."
}

setup_parse_options() {
  while (($#)); do
    case "$1" in
      --profile) setup_require_option_value "$1" "${2:-}"; PROFILE="$2"; shift 2 ;;
      --domain|--hostname) setup_require_option_value "$1" "${2:-}"; REQUESTED_HOSTNAME="$2"; shift 2 ;;
      --ip) setup_require_option_value "$1" "${2:-}"; REQUESTED_IP="$2"; shift 2 ;;
      --admin-username) setup_require_option_value "$1" "${2:-}"; ADMIN_USERNAME="$2"; shift 2 ;;
      --admin-display-name) setup_require_option_value "$1" "${2:-}"; ADMIN_DISPLAY_NAME="$2"; shift 2 ;;
      --ssh-admin-username) setup_require_option_value "$1" "${2:-}"; SSH_ADMIN_USERNAME="$2"; shift 2 ;;
      --ssh-admin-public-key-file) setup_require_option_value "$1" "${2:-}"; SSH_ADMIN_PUBLIC_KEY_FILE="$2"; shift 2 ;;
      --tls-mode) setup_require_option_value "$1" "${2:-}"; REQUESTED_TLS_MODE="$2"; shift 2 ;;
      --letsencrypt-email) setup_require_option_value "$1" "${2:-}"; REQUESTED_LETSENCRYPT_EMAIL="$2"; shift 2 ;;
      --letsencrypt-staging) REQUESTED_LETSENCRYPT_STAGING=true; shift ;;
      --skip-host) SKIP_HOST=true; shift ;;
      --no-firewall) CONFIGURE_FIREWALL=false; shift ;;
      --no-systemd) INSTALL_SYSTEMD=false; shift ;;
      --no-start) NO_START=true; shift ;;
      --regenerate-secrets) REGENERATE_SECRETS=true; shift ;;
      -h|--help) setup_usage; exit 0 ;;
      *) die "Unknown option: $1" ;;
    esac
  done
}

setup_validate_options() {
  [[ "$PROFILE" == core || "$PROFILE" == full ]] || die "--profile must be core or full."
  [[ "$ADMIN_USERNAME" =~ ^[A-Za-z0-9_.-]{3,40}$ ]] || die "Invalid admin username."
  [[ "$SSH_ADMIN_USERNAME" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || die "Invalid SSH admin username."
  if [[ -n "$SSH_ADMIN_PUBLIC_KEY_FILE" && "$SKIP_HOST" == true ]]; then
    die "--ssh-admin-public-key-file requires host provisioning; remove --skip-host."
  fi
  [[ -z "$REQUESTED_TLS_MODE" || "$REQUESTED_TLS_MODE" =~ ^(auto|letsencrypt|self-signed)$ ]] \
    || die "--tls-mode must be auto, letsencrypt, or self-signed."
}

setup_require_root_if_needed() {
  local entrypoint="$1"
  shift

  if [[ "$SKIP_HOST" == false && "$EUID" -ne 0 ]]; then
    command -v sudo >/dev/null 2>&1 || die "Please run as root or use --skip-host."
    exec sudo --preserve-env=DEBUG /usr/bin/env bash "$entrypoint" "$@"
  fi
}
