#!/usr/bin/env bash
set -Eeuo pipefail

install_host_dependencies() {
  [[ "$EUID" -eq 0 ]] || die "Host-Provisioning benötigt root-Rechte."
  export DEBIAN_FRONTEND=noninteractive

  apt-get update
  apt-get install -y ca-certificates certbot curl git openssl ufw

  if ! command -v docker >/dev/null 2>&1; then
    apt-get install -y docker.io
  fi

  if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
    apt-get install -y docker-compose-plugin 2>/dev/null \
      || apt-get install -y docker-compose-v2 2>/dev/null \
      || apt-get install -y docker-compose
  fi

  systemctl enable --now docker
  add_invoking_user_to_docker_group
}

add_invoking_user_to_docker_group() {
  local target_user="${SUDO_USER:-}"
  if [[ -n "$target_user" && "$target_user" != root ]]; then
    usermod -aG docker "$target_user"
  fi
}
