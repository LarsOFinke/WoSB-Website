#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "systemd-Installation benötigt root-Rechte."
require_command systemctl

units=(
  rbv-hub.service
  rbv-hub-backup.service
  rbv-hub-backup.timer
  rbv-hub-cert-renew.service
  rbv-hub-cert-renew.timer
)

for unit in "${units[@]}"; do
  sed "s|@INFRA_DIR@|$INFRA_DIR|g" "$INFRA_DIR/systemd/$unit" > "/etc/systemd/system/$unit"
done

# Clean migration from the pre-RBV alpha names. The old units call the same
# scripts, but leaving both timers/services enabled would duplicate work.
legacy_units=(
  blackwater-hub.service
  blackwater-hub-backup.service
  blackwater-hub-backup.timer
)
for unit in "${legacy_units[@]}"; do
  systemctl disable --now "$unit" >/dev/null 2>&1 || true
  rm -f "/etc/systemd/system/$unit"
done

systemctl daemon-reload
systemctl enable rbv-hub.service
systemctl enable --now rbv-hub-backup.timer
systemctl enable --now rbv-hub-cert-renew.timer
success "RBV systemd-Startdienst, Backup-Timer und TLS-Erneuerung wurden installiert."
