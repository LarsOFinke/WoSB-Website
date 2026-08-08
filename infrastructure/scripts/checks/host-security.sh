#!/usr/bin/env bash
set -Eeuo pipefail
export LC_ALL=C
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "The host security check requires root privileges."

systemctl is-enabled --quiet apt-daily.timer \
  || die "Automatic package-list updates are not enabled."
systemctl is-enabled --quiet apt-daily-upgrade.timer \
  || die "Automatic security installation is not enabled."
grep -Eq 'APT::Periodic::Unattended-Upgrade[[:space:]]+"1"' /etc/apt/apt.conf.d/20auto-upgrades \
  || die "unattended-upgrades is not configured to run daily."
success "Automatic security updates are enabled."

if command -v ufw >/dev/null 2>&1; then
  ufw status | grep -q '^Status: active' || die "UFW is not active."
  ufw status verbose | grep -Eq '^Default: deny \(incoming\), allow \(outgoing\)' \
    || die "UFW does not use the expected default policies."
  success "Host firewall is active with deny-incoming."
fi

docker_members="$(getent group docker | cut -d: -f4)"
if [[ -n "$docker_members" ]]; then
  warn "Docker group contains root-equivalent accounts: $docker_members"
else
  success "No interactive accounts have Docker-group privileges."
fi

if command -v sshd >/dev/null 2>&1; then
  ssh_password="$(sshd -T 2>/dev/null | awk '$1 == "passwordauthentication" {print $2; exit}' || true)"
  ssh_root="$(sshd -T 2>/dev/null | awk '$1 == "permitrootlogin" {print $2; exit}' || true)"
  [[ "$ssh_password" == no ]] \
    || warn "SSH password authentication is active. Disable it manually only after verified key access."
  [[ "$ssh_root" == no ]] \
    || warn "SSH root login is not fully disabled (${ssh_root:-unknown}). Review before public exposure."
fi
