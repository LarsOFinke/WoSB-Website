#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

backup_manifest_root() {
  local candidate="${RBF_INSTALL_ROOT:-}" runtime_data shared_data
  [[ -n "$candidate" ]] || candidate="$(realpath -m "$INFRA_DIR/../../..")"
  [[ "$candidate" == /* ]] || die "Backup installation root must be absolute: $candidate"
  candidate="$(realpath -m "$candidate")"
  if [[ -d "$INFRA_DIR/data" && -d "$candidate/shared/data" ]]; then
    runtime_data="$(realpath "$INFRA_DIR/data")"
    shared_data="$(realpath "$candidate/shared/data")"
    if [[ "$runtime_data" == "$shared_data" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  fi
  printf '%s' "$INFRA_DIR"
}

restore_database_identifier() {
  local prefix="${1:-}" epoch="${2:-$(date -u +%s)}" process_id="${3:-$$}" identifier
  [[ "$prefix" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || die "Unsafe restore database prefix."
  [[ "$epoch" =~ ^[0-9]{10,11}$ && "$process_id" =~ ^[0-9]{1,7}$ ]] \
    || die "Unsafe restore database nonce."
  identifier="${prefix}_${epoch}_${process_id}"
  # Keep generated names within the historical 32-character application
  # boundary so an incoming release can verify backups through an older active
  # schema image before the new release is activated.
  [[ "$identifier" =~ ^[A-Za-z_][A-Za-z0-9_]{1,31}$ ]] \
    || die "Generated restore database identifier exceeds the compatibility boundary."
  printf '%s\n' "$identifier"
}

backup_finalize() {
  local output="$1" category="$2"
  require_command sha256sum
  [[ -f "$output" && ! -L "$output" ]] || die "Backup artifact is missing or is not a regular file: $output"
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
    [[ -f "$metadata_checksum" ]] || die "Restore metadata has no checksum: $metadata_checksum"
    chmod 600 "$metadata" "$metadata_checksum"
    (
      cd "$directory"
      sha256sum -c "$(basename "$metadata_checksum")" >/dev/null
    ) || die "Restore metadata checksum is invalid: $metadata"
  fi

  local offsite
  offsite="$(read_env BACKUP_OFFSITE_DIR)"
  if [[ -z "$offsite" ]]; then
    if [[ -f "$INFRA_DIR/data/control/secrets/backup-remote/config.json" ]]; then
      log "No local BACKUP_OFFSITE_DIR is configured; the configured SFTP transfer is performed atomically at backup-set level."
    else
      warn "Neither BACKUP_OFFSITE_DIR nor an SFTP backup target is configured; the backup remains local only."
    fi
    return 0
  fi
  [[ "$offsite" == /* ]] || die "BACKUP_OFFSITE_DIR must be an absolute path."
  local resolved_offsite resolved_local
  resolved_offsite="$(realpath -m "$offsite")"
  resolved_local="$(realpath -m "$INFRA_DIR/data/backups")"
  [[ "$resolved_offsite" != "$resolved_local" && "$resolved_offsite" != "$resolved_local"/* ]] \
    || die "BACKUP_OFFSITE_DIR must be outside the local backup directory."

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
  ) || die "Offsite copy could not be fully verified: $destination/$filename"

  local retention_days
  retention_days="$(read_env BACKUP_RETENTION_DAYS)"
  retention_days="${retention_days:-14}"
  find "$destination" -type f -mtime "+$retention_days" -delete
  success "Atomic offsite copy with checksums created: $destination/$filename"
}

verify_backup_checksum() {
  local backup_file="$1" checksum_file="${1}.sha256"
  [[ -f "$backup_file" && ! -L "$backup_file" ]] || die "Backup is missing or is not a regular file: $backup_file"
  [[ -f "$checksum_file" && ! -L "$checksum_file" ]] || die "Required backup checksum is missing: $checksum_file"
  (
    cd "$(dirname "$backup_file")"
    sha256sum -c "$(basename "$checksum_file")"
  ) >/dev/null || die "Backup checksum is invalid: $backup_file"
}
