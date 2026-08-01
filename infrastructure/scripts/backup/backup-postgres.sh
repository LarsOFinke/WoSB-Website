#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

backup_dir="$INFRA_DIR/data/backups/postgres"
install -d -m 0700 "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="$backup_dir/rbf-${timestamp}.sql.gz"
temporary="${output}.part.$$"
committed=false
cleanup() {
  [[ "$committed" == true ]] || rm -f "$temporary" "$output" "${output}.sha256" "${output}.restore.json" "${output}.restore.json.sha256"
}
trap cleanup EXIT
user="$(read_env POSTGRES_USER)"
database="$(read_env POSTGRES_DB)"
minimum_bytes="${BACKUP_MIN_POSTGRES_BYTES:-$(read_env BACKUP_MIN_POSTGRES_BYTES)}"
minimum_bytes="${minimum_bytes:-1024}"

log "PostgreSQL-Backup wird atomar erstellt: $output"
rm -f "$temporary"
bw_compose exec -T postgres pg_dump --clean --if-exists --no-owner --no-privileges -U "$user" "$database" | gzip -9 > "$temporary"
chmod 600 "$temporary"
gzip -t "$temporary" || die "PostgreSQL-Backup ist kein gültiger gzip-Stream."
[[ "$(stat -c %s "$temporary")" -ge "$minimum_bytes" ]] || die "PostgreSQL-Backup ist ungewöhnlich klein."
mv "$temporary" "$output"

alembic_head="$(
  { bw_compose exec -T postgres psql -U "$user" -d "$database" -Atc \
      "SELECT version_num FROM alembic_version ORDER BY version_num" 2>/dev/null || true; } | paste -sd, -
)"
postgres_version="$(bw_compose exec -T postgres psql -U "$user" -d "$database" -Atc 'SHOW server_version' 2>/dev/null || true)"
git_commit="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
python3 "$INFRA_DIR/scripts/backup/backup_metadata.py" create \
  "$output" "$ENV_FILE" "$REPO_ROOT/VERSION" "$alembic_head" \
  --postgres-version "$postgres_version" \
  --git-commit "$git_commit" \
  --reason "${BACKUP_REASON:-scheduled}" \
  --format "postgresql-plain-sql+gzip" \
  --consistency "${BACKUP_CONSISTENCY_MODE:-uncoordinated}" >/dev/null
backup_finalize "$output" "postgres"
committed=true
if [[ -n "${BACKUP_RESULT_FILE:-}" ]]; then
  printf '%s\n' "$output" > "$BACKUP_RESULT_FILE"
  chmod 600 "$BACKUP_RESULT_FILE"
fi
retention_days="$(read_env BACKUP_RETENTION_DAYS)"; retention_days="${retention_days:-14}"
find "$backup_dir" -type f -mtime "+$retention_days" -delete
success "PostgreSQL-Backup erstellt: $output"
