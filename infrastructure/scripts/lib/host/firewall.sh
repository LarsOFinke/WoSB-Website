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
    warn "Firewall-Konfiguration übersprungen (keine root-Rechte)."
    return 0
  fi

  local ssh_port
  ssh_port="$(detect_ssh_port)"
  ufw allow "${ssh_port}/tcp"
  ufw allow 80/tcp
  ufw allow 443/tcp
  configure_monitoring_firewall_rule
  ufw --force enable
}

configure_monitoring_firewall_rule() {
  is_true "$(read_env ENABLE_MONITORING)" || return 0

  local monitoring_port
  monitoring_port="$(read_env MONITORING_HTTPS_PORT)"
  [[ "$monitoring_port" =~ ^[0-9]+$ ]] || monitoring_port=8443
  ufw allow "${monitoring_port}/tcp"
}
