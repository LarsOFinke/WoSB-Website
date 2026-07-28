#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

backup_dir="$INFRA_DIR/data/backups/postgres"
mkdir -p "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="$backup_dir/rbf-${timestamp}.sql.gz"
user="$(read_env POSTGRES_USER)"
database="$(read_env POSTGRES_DB)"

log "PostgreSQL-Backup wird erstellt: $output"
bw_compose exec -T postgres pg_dump --clean --if-exists --no-owner --no-privileges -U "$user" "$database" | gzip -9 > "$output"
backup_finalize "$output" "postgres"
if [[ -n "${BACKUP_RESULT_FILE:-}" ]]; then
  printf '%s\n' "$output" > "$BACKUP_RESULT_FILE"
  chmod 600 "$BACKUP_RESULT_FILE"
fi
retention_days="$(read_env BACKUP_RETENTION_DAYS)"
retention_days="${retention_days:-14}"
find "$backup_dir" -type f -mtime "+$retention_days" -delete
success "PostgreSQL-Backup erstellt: $output"
