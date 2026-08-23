#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "systemd installation requires root privileges."
require_command systemctl

units=(
  rbf-hub.service
  rbf-hub-backup-admin.service
  rbf-hub-backup-admin.path
  rbf-hub-backup-pull.service
  rbf-hub-backup-pull.path
  rbf-hub-cert-renew.service
  rbf-hub-cert-renew.timer
  rbf-hub-update.service
  rbf-hub-update.path
)

deployment_environment="$(read_env DEPLOYMENT_ENVIRONMENT)"
[[ "$deployment_environment" == test || "$deployment_environment" == production ]] \
  || die "DEPLOYMENT_ENVIRONMENT must be test or production before installing systemd units."

systemd_infra="${RBF_SYSTEMD_INFRA_DIR:-$INFRA_DIR}"
for unit in "${units[@]}"; do
  sed -e "s|@INFRA_DIR@|$systemd_infra|g" \
      -e "s|@BACKUP_ENVIRONMENT@|$deployment_environment|g" \
      "$INFRA_DIR/systemd/$unit" > "/etc/systemd/system/$unit"
done

# Remove the retired scheduled/push backup chain as well as pre-RBF unit names.
# Recovery Tool pulls and owner-approved admin operations are the only runtime
# backup dispatchers now.
retired_backup_units=(
  rbf-hub-backup.service
  rbf-hub-backup.timer
)
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
for unit in "${retired_backup_units[@]}" "${legacy_units[@]}"; do
  systemctl disable --now "$unit" >/dev/null 2>&1 || true
  rm -f "/etc/systemd/system/$unit"
done

systemctl daemon-reload
systemctl enable rbf-hub.service
if [[ -n "$(read_env BACKUP_PULL_ENROLLMENT_ID)" ]]; then
  systemctl enable --now rbf-hub-backup-pull.path
else
  systemctl disable --now rbf-hub-backup-pull.path >/dev/null 2>&1 || true
fi
systemctl enable --now rbf-hub-backup-admin.path
systemctl enable --now rbf-hub-cert-renew.timer
systemctl enable --now rbf-hub-update.path
success "RBF systemd startup service and backup/TLS/update watchers were installed."
