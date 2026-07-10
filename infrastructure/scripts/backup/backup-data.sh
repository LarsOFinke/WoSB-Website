#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$INFRA_DIR/data/backups/files"
output="$backup_dir/blackwater-files-${timestamp}.tar.gz"
mkdir -p "$backup_dir"

tar --exclude='backups' -czf "$output" -C "$INFRA_DIR/data" uploads certs uptime-kuma
chmod 600 "$output"
retention_days="$(read_env BACKUP_RETENTION_DAYS)"
retention_days="${retention_days:-14}"
find "$backup_dir" -type f -mtime "+$retention_days" -delete
success "Datei-Backup erstellt: $output"
