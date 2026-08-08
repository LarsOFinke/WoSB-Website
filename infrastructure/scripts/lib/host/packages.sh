#!/usr/bin/env bash
set -Eeuo pipefail

install_host_dependencies() {
  [[ "$EUID" -eq 0 ]] || die "Host provisioning requires root privileges."
  export DEBIAN_FRONTEND=noninteractive

  apt-get update
  apt-get install -y age ca-certificates certbot curl git openssh-client openssl ufw unattended-upgrades

  if ! command -v docker >/dev/null 2>&1; then
    apt-get install -y docker.io
  fi

  if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
    apt-get install -y docker-compose-plugin 2>/dev/null \
      || apt-get install -y docker-compose-v2 2>/dev/null \
      || apt-get install -y docker-compose
  fi

  systemctl enable --now docker
  install -m 0644 "$INFRA_DIR/config/host/20auto-upgrades" /etc/apt/apt.conf.d/20auto-upgrades
  install -m 0644 "$INFRA_DIR/config/host/52rbf-unattended-upgrades" /etc/apt/apt.conf.d/52rbf-unattended-upgrades
  systemctl enable --now apt-daily.timer apt-daily-upgrade.timer
  success "Automatic security updates are active; required restarts remain administratively controlled."
}
