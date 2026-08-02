#!/usr/bin/env bash
set -Eeuo pipefail
export LC_ALL=C
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "Der Host-Security-Check benötigt root-Rechte."

systemctl is-enabled --quiet apt-daily.timer \
  || die "Automatische Paketlisten-Aktualisierung ist nicht aktiviert."
systemctl is-enabled --quiet apt-daily-upgrade.timer \
  || die "Automatische Security-Installation ist nicht aktiviert."
grep -Eq 'APT::Periodic::Unattended-Upgrade[[:space:]]+"1"' /etc/apt/apt.conf.d/20auto-upgrades \
  || die "unattended-upgrades ist nicht täglich konfiguriert."
success "Automatische Security-Updates sind aktiviert."

if command -v ufw >/dev/null 2>&1; then
  ufw status | grep -q '^Status: active' || die "UFW ist nicht aktiv."
  ufw status verbose | grep -Eq '^Default: deny \(incoming\), allow \(outgoing\)' \
    || die "UFW verwendet nicht die erwarteten Default-Policies."
  success "Host-Firewall ist mit deny-incoming aktiv."
fi

docker_members="$(getent group docker | cut -d: -f4)"
if [[ -n "$docker_members" ]]; then
  warn "Docker-Gruppe enthält root-äquivalente Konten: $docker_members"
else
  success "Keine interaktiven Konten besitzen Docker-Gruppenrechte."
fi

if command -v sshd >/dev/null 2>&1; then
  ssh_password="$(sshd -T 2>/dev/null | awk '$1 == "passwordauthentication" {print $2; exit}' || true)"
  ssh_root="$(sshd -T 2>/dev/null | awk '$1 == "permitrootlogin" {print $2; exit}' || true)"
  [[ "$ssh_password" == no ]] \
    || warn "SSH-Passwortauthentifizierung ist aktiv. Erst nach geprüftem Schlüsselzugang manuell deaktivieren."
  [[ "$ssh_root" == no ]] \
    || warn "SSH-Root-Login ist nicht vollständig deaktiviert (${ssh_root:-unbekannt}). Vor öffentlicher Freigabe prüfen."
fi
