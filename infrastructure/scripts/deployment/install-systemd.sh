#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "systemd-Installation benötigt root-Rechte."
require_command systemctl

units=(
  rbf-hub.service
  rbf-hub-backup.service
  rbf-hub-backup.timer
  rbf-hub-cert-renew.service
  rbf-hub-cert-renew.timer
  rbf-hub-update.service
  rbf-hub-update.path
)

for unit in "${units[@]}"; do
  sed "s|@INFRA_DIR@|$INFRA_DIR|g" "$INFRA_DIR/systemd/$unit" > "/etc/systemd/system/$unit"
done

# Clean migration from the pre-RBF alpha names. The old units call the same
# scripts, but leaving both timers/services enabled would duplicate work.
legacy_units=(
  rbv-hub.service
  rbv-hub-backup.service
  rbv-hub-backup.timer
  rbv-hub-cert-renew.service
  rbv-hub-cert-renew.timer
  blackwater-hub.service
  blackwater-hub-backup.service
  blackwater-hub-backup.timer
)
for unit in "${legacy_units[@]}"; do
  systemctl disable --now "$unit" >/dev/null 2>&1 || true
  rm -f "/etc/systemd/system/$unit"
done


systemctl daemon-reload
systemctl enable rbf-hub.service
systemctl enable --now rbf-hub-backup.timer
systemctl enable --now rbf-hub-cert-renew.timer
systemctl enable --now rbf-hub-update.path
success "RBF systemd-Startdienst, Backup-/TLS-Timer und Admin-Update-Runner wurden installiert."
