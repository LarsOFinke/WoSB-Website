#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "systemd-Installation benötigt root-Rechte."
require_command systemctl

units=(
  rbf-hub.service
  rbf-hub-backup.service
  rbf-hub-backup.timer
  rbf-hub-backup-admin.service
  rbf-hub-backup-admin.path
  rbf-hub-cert-renew.service
  rbf-hub-cert-renew.timer
)

systemd_infra="${RBF_SYSTEMD_INFRA_DIR:-$INFRA_DIR}"
for unit in "${units[@]}"; do
  sed "s|@INFRA_DIR@|$systemd_infra|g" "$INFRA_DIR/systemd/$unit" > "/etc/systemd/system/$unit"
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
systemctl disable --now rbf-hub-update.path rbf-hub-update.service >/dev/null 2>&1 || true
rm -f /etc/systemd/system/rbf-hub-update.path /etc/systemd/system/rbf-hub-update.service
systemctl daemon-reload
systemctl enable rbf-hub.service
systemctl enable --now rbf-hub-backup.timer
systemctl enable --now rbf-hub-backup-admin.path
systemctl enable --now rbf-hub-cert-renew.timer
success "RBF systemd-Startdienst sowie Backup-/TLS-Timer wurden installiert. Updates laufen ausschließlich über den Ursprungsserver."
