#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$INFRA_DIR/data/backups/files"
output="$backup_dir/rbf-files-${timestamp}.tar.gz"
install -d -m 0700 "$backup_dir"
install -d -m 0750 "$INFRA_DIR/data/uploads"

backup_paths=(uploads)
for optional_path in certs letsencrypt uptime-kuma; do
  if [[ -e "$INFRA_DIR/data/$optional_path" ]]; then
    backup_paths+=("$optional_path")
  else
    warn "Optionaler Backup-Pfad fehlt und wird übersprungen: $optional_path"
  fi
done

tar --exclude='backups' -czf "$output" -C "$INFRA_DIR/data" "${backup_paths[@]}"
backup_finalize "$output" "files"
if [[ -n "${BACKUP_RESULT_FILE:-}" ]]; then
  printf '%s\n' "$output" > "$BACKUP_RESULT_FILE"
  chmod 600 "$BACKUP_RESULT_FILE"
fi
retention_days="$(read_env BACKUP_RETENTION_DAYS)"
retention_days="${retention_days:-14}"
find "$backup_dir" -type f -mtime "+$retention_days" -delete
success "Datei-Backup erstellt: $output"
