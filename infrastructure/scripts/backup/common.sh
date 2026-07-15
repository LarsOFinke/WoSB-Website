#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

backup_finalize() {
  local output="$1" category="$2"
  require_command sha256sum
  local directory filename checksum
  directory="$(dirname "$output")"
  filename="$(basename "$output")"
  checksum="${output}.sha256"
  (
    cd "$directory"
    sha256sum "$filename" > "${filename}.sha256"
  )
  chmod 600 "$output" "$checksum"

  local offsite
  offsite="$(read_env BACKUP_OFFSITE_DIR)"
  if [[ -z "$offsite" ]]; then
    warn "Kein BACKUP_OFFSITE_DIR konfiguriert; Backup bleibt ausschließlich lokal."
    return 0
  fi
  [[ "$offsite" == /* ]] || die "BACKUP_OFFSITE_DIR muss ein absoluter Pfad sein."
  local resolved_offsite resolved_local
  resolved_offsite="$(realpath -m "$offsite")"
  resolved_local="$(realpath -m "$INFRA_DIR/data/backups")"
  [[ "$resolved_offsite" != "$resolved_local" && "$resolved_offsite" != "$resolved_local"/* ]] \
    || die "BACKUP_OFFSITE_DIR muss außerhalb des lokalen Backup-Verzeichnisses liegen."

  local destination="$resolved_offsite/$category"
  install -d -m 0700 "$destination"
  install -m 0600 "$output" "$checksum" "$destination/"
  (
    cd "$destination"
    sha256sum -c "${filename}.sha256" >/dev/null
  )

  local retention_days
  retention_days="$(read_env BACKUP_RETENTION_DAYS)"
  retention_days="${retention_days:-14}"
  find "$destination" -type f -mtime "+$retention_days" -delete
  success "Offsite-Kopie mit Prüfsumme erstellt: $destination/$filename"
}

verify_backup_checksum() {
  local backup_file="$1" checksum_file="${1}.sha256"
  [[ -f "$checksum_file" ]] || {
    warn "Keine Prüfsumme neben dem Backup gefunden: $checksum_file"
    return 0
  }
  (
    cd "$(dirname "$backup_file")"
    sha256sum -c "$(basename "$checksum_file")"
  ) || die "Backup-Prüfsumme ist ungültig: $backup_file"
}
