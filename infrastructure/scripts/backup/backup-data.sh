#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$INFRA_DIR/data/backups/files"
output="$backup_dir/rbf-files-${timestamp}.tar.gz"
temporary="${output}.part.$$"
committed=false
cleanup() { [[ "$committed" == true ]] || rm -f "$temporary" "$output" "${output}.sha256"; }
trap cleanup EXIT
install -d -m 0700 "$backup_dir"
install -d -m 0750 "$INFRA_DIR/data/uploads"
minimum_bytes="${BACKUP_MIN_FILES_BYTES:-$(read_env BACKUP_MIN_FILES_BYTES)}"; minimum_bytes="${minimum_bytes:-64}"
backup_paths=(uploads)
for optional_path in certs letsencrypt uptime-kuma; do
  if [[ -e "$INFRA_DIR/data/$optional_path" ]]; then backup_paths+=("$optional_path"); else warn "Optionaler Backup-Pfad fehlt und wird übersprungen: $optional_path"; fi
done
rm -f "$temporary"
tar --exclude='backups' -czf "$temporary" -C "$INFRA_DIR/data" "${backup_paths[@]}"
chmod 600 "$temporary"
tar -tzf "$temporary" >/dev/null || die "Datei-Backup ist kein gültiges tar.gz-Archiv."
[[ "$(stat -c %s "$temporary")" -ge "$minimum_bytes" ]] || die "Datei-Backup ist ungewöhnlich klein."
mv "$temporary" "$output"
backup_finalize "$output" "files"
committed=true
if [[ -n "${BACKUP_RESULT_FILE:-}" ]]; then printf '%s\n' "$output" > "$BACKUP_RESULT_FILE"; chmod 600 "$BACKUP_RESULT_FILE"; fi
retention_days="$(read_env BACKUP_RETENTION_DAYS)"; retention_days="${retention_days:-14}"
find "$backup_dir" -type f -mtime "+$retention_days" -delete
success "Datei-Backup erstellt: $output"
