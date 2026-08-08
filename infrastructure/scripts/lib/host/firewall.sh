#!/usr/bin/env bash
set -Eeuo pipefail

detect_ssh_port() {
  local port=""
  if command -v sshd >/dev/null 2>&1; then
    port="$(sshd -T 2>/dev/null | awk '$1 == "port" {print $2; exit}' || true)"
  fi
  if [[ ! "$port" =~ ^[0-9]+$ && -r /etc/ssh/sshd_config ]]; then
    port="$(awk 'tolower($1) == "port" {print $2; exit}' /etc/ssh/sshd_config || true)"
  fi
  [[ "$port" =~ ^[0-9]+$ ]] || port=22
  printf '%s' "$port"
}

configure_firewall() {
  if [[ "$EUID" -ne 0 ]]; then
    warn "Firewall configuration skipped (no root privileges)."
    return 0
  fi

  local ssh_port
  ssh_port="$(detect_ssh_port)"
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow "${ssh_port}/tcp"
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
}
