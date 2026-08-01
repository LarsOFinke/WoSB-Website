#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

backup_finalize() {
  local output="$1" category="$2"
  require_command sha256sum
  [[ -f "$output" && ! -L "$output" ]] || die "Backup-Artefakt fehlt oder ist kein reguläres File: $output"
  local directory filename checksum
  directory="$(dirname "$output")"
  filename="$(basename "$output")"
  checksum="${output}.sha256"
  (
    cd "$directory"
    sha256sum "$filename" > "${filename}.sha256"
  )
  chmod 600 "$output" "$checksum"
  local metadata="${output}.restore.json" metadata_checksum="${output}.restore.json.sha256"
  if [[ -f "$metadata" ]]; then
    [[ -f "$metadata_checksum" ]] || die "Restore-Metadaten haben keine Prüfsumme: $metadata_checksum"
    chmod 600 "$metadata" "$metadata_checksum"
    (
      cd "$directory"
      sha256sum -c "$(basename "$metadata_checksum")" >/dev/null
    ) || die "Restore-Metadaten-Prüfsumme ist ungültig: $metadata"
  fi

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

  local destination="$resolved_offsite/$category" source target temporary
  install -d -m 0700 "$destination"
  for source in "$output" "$checksum"; do
    target="$destination/$(basename "$source")"
    temporary="${target}.part.$$"
    install -m 0600 "$source" "$temporary"
    mv -f "$temporary" "$target"
  done
  if [[ -f "$metadata" ]]; then
    for source in "$metadata" "$metadata_checksum"; do
      target="$destination/$(basename "$source")"
      temporary="${target}.part.$$"
      install -m 0600 "$source" "$temporary"
      mv -f "$temporary" "$target"
    done
  fi
  (
    cd "$destination"
    sha256sum -c "${filename}.sha256" >/dev/null
    if [[ -f "${filename}.restore.json.sha256" ]]; then
      sha256sum -c "${filename}.restore.json.sha256" >/dev/null
    fi
  ) || die "Offsite-Kopie konnte nicht vollständig verifiziert werden: $destination/$filename"

  local retention_days
  retention_days="$(read_env BACKUP_RETENTION_DAYS)"
  retention_days="${retention_days:-14}"
  find "$destination" -type f -mtime "+$retention_days" -delete
  success "Atomare Offsite-Kopie mit Prüfsummen erstellt: $destination/$filename"
}

verify_backup_checksum() {
  local backup_file="$1" checksum_file="${1}.sha256"
  [[ -f "$backup_file" && ! -L "$backup_file" ]] || die "Backup fehlt oder ist kein reguläres File: $backup_file"
  [[ -f "$checksum_file" && ! -L "$checksum_file" ]] || die "Verpflichtende Backup-Prüfsumme fehlt: $checksum_file"
  (
    cd "$(dirname "$backup_file")"
    sha256sum -c "$(basename "$checksum_file")"
  ) >/dev/null || die "Backup-Prüfsumme ist ungültig: $backup_file"
}
