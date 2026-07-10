#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "systemd-Installation benötigt root-Rechte."
require_command systemctl

for unit in blackwater-hub.service blackwater-hub-backup.service blackwater-hub-backup.timer; do
  sed "s|@INFRA_DIR@|$INFRA_DIR|g" "$INFRA_DIR/systemd/$unit" > "/etc/systemd/system/$unit"
done

systemctl daemon-reload
systemctl enable blackwater-hub.service
systemctl enable --now blackwater-hub-backup.timer
success "systemd-Startdienst und täglicher Backup-Timer wurden installiert."
