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
  rbf-hub-discord-bot-manager.service
  rbf-hub-discord-bot-manager.path
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

install -d -m 0750 /etc/rbf-hub
if [[ ! -f /etc/rbf-hub/discord-bot-manager.env ]]; then
  install -m 0600 "$INFRA_DIR/config/discord-bot-manager.env.example" /etc/rbf-hub/discord-bot-manager.env
else
  ensure_manager_default() {
    local key="$1" value="$2"
    grep -qE "^${key}=" /etc/rbf-hub/discord-bot-manager.env \
      || printf '\n%s=%s\n' "$key" "$value" >> /etc/rbf-hub/discord-bot-manager.env
  }
  ensure_manager_default RBF_DISCORD_BOT_BIND_HOST 0.0.0.0
  ensure_manager_default RBF_DISCORD_BOT_FIREWALL_MODE auto
  chmod 0600 /etc/rbf-hub/discord-bot-manager.env
fi

systemctl daemon-reload
systemctl enable rbf-hub.service
systemctl enable --now rbf-hub-backup.timer
systemctl enable --now rbf-hub-cert-renew.timer
systemctl enable --now rbf-hub-update.path
systemctl enable --now rbf-hub-discord-bot-manager.path
/usr/bin/env bash "$INFRA_DIR/scripts/services/manage-discord-bot.sh" --status-only || true
success "RBF systemd-Startdienst, Backup-/TLS-Timer und Admin-Update-Runner und Discord-Bot-Manager wurden installiert."
