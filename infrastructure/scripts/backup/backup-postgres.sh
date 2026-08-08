#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

backup_dir="$INFRA_DIR/data/backups/postgres"
install -d -m 0700 "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="$backup_dir/rbf-postgres-${timestamp}.dump"
temporary="${output}.part.$$"
metadata="${output}.restore.json"
committed=false
cleanup() { [[ "$committed" == true ]] || rm -f "$temporary" "$output" "$metadata" "${output}.sha256" "${metadata}.sha256"; }
trap cleanup EXIT
user="$(read_env POSTGRES_USER)"; database="$(read_env POSTGRES_DB)"
minimum_bytes="${BACKUP_MIN_POSTGRES_BYTES:-$(read_env BACKUP_MIN_POSTGRES_BYTES)}"; minimum_bytes="${minimum_bytes:-1024}"

log "Erzeuge atomaren PostgreSQL-Custom-Dump."
bw_compose exec -T postgres pg_dump --format=custom --compress=9 --no-owner --no-privileges -U "$user" "$database" > "$temporary"
chmod 600 "$temporary"
[[ "$(stat -c %s "$temporary")" -ge "$minimum_bytes" ]] || die "PostgreSQL backup is unusually small."
bw_compose exec -T postgres pg_restore --list < "$temporary" >/dev/null || die "PostgreSQL dump is not readable."
mv "$temporary" "$output"

flyway_version="$(bw_compose exec -T postgres psql -U "$user" -d "$database" -Atqc \
  "select coalesce(max(version),'') from flyway_schema_history where success" 2>/dev/null || true)"
backup_sha="$(sha256sum "$output" | awk '{print $1}')"
backup_size="$(stat -c %s "$output")"
cat > "$metadata" <<JSON
{
  "schema_version": 2,
  "kind": "rbf-postgresql-backup",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup": {
    "filename": "$(basename "$output")",
    "size_bytes": $backup_size,
    "sha256": "$backup_sha",
    "format": "postgres-custom",
    "consistency": "${BACKUP_CONSISTENCY_MODE:-application-quiesced}",
    "reason": "${BACKUP_REASON:-manual}"
  },
  "application": {
    "version": "$(cat "$REPO_ROOT/VERSION" 2>/dev/null || printf unknown)",
    "flyway_version": "$flyway_version"
  },
  "security": {"secret_key_fingerprints": []}
}
JSON
chmod 600 "$metadata"
(
  cd "$backup_dir"
  sha256sum "$(basename "$metadata")" > "$(basename "$metadata").sha256"
)
backup_finalize "$output" postgres
committed=true
[[ -z "${BACKUP_RESULT_FILE:-}" ]] || { printf '%s\n' "$output" > "$BACKUP_RESULT_FILE"; chmod 600 "$BACKUP_RESULT_FILE"; }
retention_days="$(read_env BACKUP_RETENTION_DAYS)"; retention_days="${retention_days:-14}"
find "$backup_dir" -type f -mtime "+$retention_days" -delete
success "PostgreSQL backup created: $output"
