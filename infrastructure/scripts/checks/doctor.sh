#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$INFRA_DIR/scripts/backup/common.sh"

"$INFRA_DIR/scripts/checks/preflight.sh" runtime
validate_env
bw_compose_with_profiles config >/dev/null
success "Compose- und Umgebungs-Konfiguration sind gültig."

log "Containerstatus"
bw_compose_with_profiles ps

log "Speicherbelegung"
df -h "$INFRA_DIR"

backup_count="$(find "$INFRA_DIR/data/backups" -mindepth 2 -type f ! -name '*.sha256' 2>/dev/null | wc -l | tr -d ' ')"
log "Lokale Backup-Dateien: ${backup_count:-0}"

if is_true "$(read_env BACKUP_RECOVERY_ENABLED)"; then
  recipient="$(read_env BACKUP_AGE_RECIPIENT)"
  [[ "$recipient" =~ ^age1[0-9a-z]{20,}$ ]]     || die "Recovery-Backup ist aktiviert, aber BACKUP_AGE_RECIPIENT ist ungültig."
  latest_recovery="$(find "$INFRA_DIR/data/backups/recovery" -maxdepth 1 -type f -name 'rbf-recovery-*.tar.gz.age' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
  if [[ -n "$latest_recovery" ]]; then
    verify_backup_checksum "$latest_recovery"
    log "Neuestes verschlüsseltes Recovery-Bundle: $latest_recovery"
  else
    warn "Recovery-Backup ist aktiviert, aber es existiert noch kein Bundle."
  fi
  export_dir="$(read_env BACKUP_PULL_EXPORT_DIR)"
  export_user="$(read_env BACKUP_PULL_EXPORT_USER)"
  if [[ -n "$export_dir" || -n "$export_user" ]]; then
    [[ -n "$export_dir" && -n "$export_user" ]]       || die "BACKUP_PULL_EXPORT_DIR und BACKUP_PULL_EXPORT_USER müssen gemeinsam gesetzt sein."
    [[ -d "$export_dir" ]] || warn "Pull-Export-Verzeichnis existiert noch nicht: $export_dir"
    id "$export_user" >/dev/null 2>&1 || die "Pull-Export-Benutzer existiert nicht: $export_user"
  fi
else
  warn "Vollständiges verschlüsseltes Disaster-Recovery ist deaktiviert."
fi

if bw_compose ps --status running api gateway postgres 2>/dev/null | grep -q .; then
  "$INFRA_DIR/scripts/checks/smoke-test.sh"
else
  warn "Mindestens ein Kernservice läuft nicht; Smoke-Test wurde übersprungen."
fi
