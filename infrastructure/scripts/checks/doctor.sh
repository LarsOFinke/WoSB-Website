#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"

"$INFRA_DIR/scripts/checks/preflight.sh" runtime
validate_env
bw_compose_with_profiles config >/dev/null
success "Compose- und Umgebungs-Konfiguration sind gültig."

log "Containerstatus"
bw_compose_with_profiles ps

log "Speicherbelegung"
df -h "$INFRA_DIR"

backup_count="$(find "$INFRA_DIR/data/backups" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')"
log "Lokale Backup-Dateien: ${backup_count:-0}"

if bw_compose ps --status running api gateway postgres 2>/dev/null | grep -q .; then
  "$INFRA_DIR/scripts/checks/smoke-test.sh"
else
  warn "Mindestens ein Kernservice läuft nicht; Smoke-Test wurde übersprungen."
fi
