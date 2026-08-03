#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
source "$INFRA_DIR/scripts/lib/maintenance.sh"

usage() {
  cat <<'USAGE'
Usage:
  sudo restore-postgres.sh [--preflight-only] [--report FILE]
    [--allow-legacy-metadata] [--allow-uncoordinated] BACKUP.sql[.gz]

A full preflight imports into an isolated staging database, assesses Alembic
compatibility, migrates to the current head, validates encrypted data and starts
the current API image for a real readiness check. --preflight-only never changes
the active database.
USAGE
}

preflight_only=false
allow_legacy=false
allow_uncoordinated=false
report_path=""
backup_argument=""
while (($#)); do
  case "$1" in
    --preflight-only) preflight_only=true; shift ;;
    --allow-legacy-metadata) allow_legacy=true; shift ;;
    --allow-uncoordinated) allow_uncoordinated=true; shift ;;
    --report) report_path="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --*) die "Unbekannte Restore-Option: $1" ;;
    *) [[ -z "$backup_argument" ]] || die "Nur ein PostgreSQL-Backup darf angegeben werden."; backup_argument="$1"; shift ;;
  esac
done

[[ -n "$backup_argument" ]] || die "PostgreSQL-Backup fehlt."
[[ "$EUID" -eq 0 ]] || die "PostgreSQL-Restores benötigen root-Rechte."
require_command flock
require_command python3
backup_file="$(realpath "$backup_argument")"
[[ -f "$backup_file" ]] || die "Backup nicht gefunden: $backup_file"
verify_backup_checksum "$backup_file"
metadata_file="${backup_file}.restore.json"
report_script="$INFRA_DIR/scripts/backup/recovery_report.py"
preflight_script="$INFRA_DIR/scripts/backup/recovery_preflight.py"
metadata_script="$INFRA_DIR/scripts/backup/backup_metadata.py"
if [[ -z "$report_path" ]]; then
  install -d -m 0700 "$INFRA_DIR/data/backups/reports"
  report_path="$INFRA_DIR/data/backups/reports/rbf-postgres-$([[ "$preflight_only" == true ]] && printf preflight || printf restore)-$(date -u +%Y%m%dT%H%M%SZ)-$$.json"
fi
report_path="$(realpath -m "$report_path")"
python3 "$report_script" create "$report_path" \
  --mode "$([[ "$preflight_only" == true ]] && printf preflight || printf restore)" \
  --source "$backup_file" --source-file "$backup_file" >/dev/null
report_finished=false
report_check() {
  local name="$1" status="$2" detail="$3" data="${4:-}"
  local args=(add "$report_path" --name "$name" --status "$status" --detail "$detail")
  [[ -z "$data" ]] || args+=(--data-json "$data")
  python3 "$report_script" "${args[@]}" >/dev/null
}
finish_report() {
  local status="$1" recoverable="$2"
  python3 "$report_script" finish "$report_path" --status "$status" --recoverable "$recoverable" >/dev/null
  backup_finalize "$report_path" "reports"
  report_finished=true
}

user="$(read_env POSTGRES_USER)"
database="$(read_env POSTGRES_DB)"
database_url="$(read_env DATABASE_URL)"
[[ "$database" =~ ^[A-Za-z_][A-Za-z0-9_]{0,62}$ ]] || die "POSTGRES_DB ist kein sicher unterstützter PostgreSQL-Bezeichner."
[[ "$user" =~ ^[A-Za-z_][A-Za-z0-9_]{0,62}$ ]] || die "POSTGRES_USER ist kein sicher unterstützter PostgreSQL-Bezeichner."

restore_lock="$INFRA_DIR/data/control/run/update.lock"
mkdir -p "$(dirname "$restore_lock")"
if [[ "${RBF_RESTORE_LOCK_HELD:-false}" != true ]]; then
  exec 9>"$restore_lock"
  flock -n 9 || die "Update, Restore oder eine andere exklusive Serveroperation läuft bereits."
fi

suffix="$(date -u +%m%d%H%M%S)-$$"
staging_database="${database}_restore_${suffix}"; staging_database="${staging_database:0:63}"
rollback_database="${database}_rollback_${suffix}"; rollback_database="${rollback_database:0:63}"
failed_database="${database}_failed_${suffix}"; failed_database="${failed_database:0:63}"
restore_completed=false
maintenance_mode=false
MAINTENANCE_ACTIVE=false
swap_completed=false
staging_created=false

url_for_database() {
  python3 - "$database_url" "$1" <<'PY'
from urllib.parse import urlsplit, urlunsplit
import sys
url, database = sys.argv[1:]
parts = urlsplit(url)
print(urlunsplit((parts.scheme, parts.netloc, f"/{database}", parts.query, parts.fragment)))
PY
}
postgres_admin() { bw_compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$user" -d postgres "$@"; }
drop_database_if_exists() {
  local name="$1"
  postgres_admin -v database_name="$name" <<'SQL'
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'database_name') \gexec
SQL
}
start_application_best_effort() {
  bw_compose up -d --no-deps api || return 1
  wait_for_api || return 1
  bw_compose up -d --no-deps gateway || return 1
  ensure_monitoring_services || return 1
  /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh" || return 1
}
rollback_database_swap() {
  warn "Die neue Datenbank bestand den Anwendungstest nicht; stelle die vorherige Datenbank atomar wieder her."
  bw_compose stop api >/dev/null 2>&1 || true
  postgres_admin -v target_db="$database" -v rollback_db="$rollback_database" -v failed_db="$failed_database" <<'SQL'
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE datname IN (:'target_db', :'rollback_db') AND pid <> pg_backend_pid();
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'failed_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'target_db', :'failed_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'rollback_db', :'target_db') \gexec
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'failed_db') \gexec
SQL
  swap_completed=false
  start_application_best_effort
}
cleanup_on_exit() {
  local exit_code=$?
  set +e
  if [[ "$exit_code" -ne 0 && "$restore_completed" != true ]]; then
    if [[ "$swap_completed" == true ]]; then rollback_database_swap || true
    elif [[ "$maintenance_mode" == true ]]; then start_application_best_effort || true
    fi
  fi
  if [[ "$staging_created" == true ]]; then
    drop_database_if_exists "$staging_database" >/dev/null 2>&1 || true
    report_check preflight_cleanup passed "Temporary staging database was removed." >/dev/null 2>&1 || true
  fi
  if [[ "$report_finished" != true ]]; then
    report_check preflight_cleanup "$([[ "$staging_created" == true ]] && printf passed || printf skipped)" "Preflight cleanup completed during error handling." >/dev/null 2>&1 || true
    python3 "$report_script" finish "$report_path" --status failed --recoverable false >/dev/null 2>&1 || true
    backup_finalize "$report_path" "reports" >/dev/null 2>&1 || true
  fi
  [[ "$MAINTENANCE_ACTIVE" != true ]] \
    || maintenance_disable failed "Database restore failed (exit ${exit_code}); the previous database was restored where possible."
  exit "$exit_code"
}
trap cleanup_on_exit EXIT

if [[ -f "$metadata_file" ]]; then
  verify_backup_checksum "$metadata_file"
  python3 "$metadata_script" validate "$metadata_file" "$backup_file" >/dev/null
  migrations_root="${RBF_ARTIFACT_ROOT:-$REPO_ROOT}"
  preflight_args=(--metadata "$metadata_file" --migrations-dir "$migrations_root/backend/migrations/versions")
  [[ "$allow_legacy" == true ]] && preflight_args+=(--allow-unrecorded)
  [[ "$allow_uncoordinated" == true ]] && preflight_args+=(--allow-uncoordinated)
  compatibility_json="$(python3 "$preflight_script" "${preflight_args[@]}")" \
    || die "Restore-Metadaten oder Alembic-Kompatibilität wurden abgelehnt."
  report_check metadata_compatibility passed "Restore metadata, consistency mode and Alembic graph are compatible." "$compatibility_json"
else
  [[ "$allow_legacy" == true ]] || die "Restore-Metadaten fehlen. Nur Root-CLI darf dies bewusst mit --allow-legacy-metadata übersteuern."
  report_check metadata_compatibility warning "Legacy backup without restore metadata was explicitly accepted; full staging validation remains mandatory."
fi

ensure_postgres_service
if [[ "$preflight_only" != true ]]; then
  log "Erzeuge vor dem Restore einen koordinierten Sicherheits-Wiederherstellungspunkt."
  RBF_BACKUP_LOCK_HELD=true /usr/bin/env bash "$INFRA_DIR/scripts/backup/run-consistent-backup.sh" \
    --lock-held --reason pre-restore
fi

log "Erzeuge eine isolierte Staging-Datenbank."
postgres_admin -v staging_db="$staging_database" -v database_owner="$user" <<'SQL'
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'staging_db') \gexec
SELECT format('CREATE DATABASE %I OWNER %I TEMPLATE template0', :'staging_db', :'database_owner') \gexec
SQL
staging_created=true
report_check staging_database_creation passed "Isolated staging database was created without changing production."

log "Importiere PostgreSQL-Backup transaktional in die Staging-Datenbank."
if [[ "$backup_file" == *.gz ]]; then
  gzip -dc "$backup_file" | bw_compose exec -T postgres psql -1 -v ON_ERROR_STOP=1 -U "$user" "$staging_database"
else
  bw_compose exec -T postgres psql -1 -v ON_ERROR_STOP=1 -U "$user" "$staging_database" < "$backup_file"
fi
report_check postgres_import passed "PostgreSQL accepted the complete dump transactionally."

staging_url="$(url_for_database "$staging_database")"
runtime_env_args=(
  -e "CONTROL_REQUEST_DIR=/tmp/rbf-control/inbox"
  -e "CONTROL_STATUS_DIR=/tmp/rbf-control/status"
)
if [[ -n "${RBF_RESTORE_WEBHOOK_KEYS:-}" ]]; then
  runtime_env_args+=(-e "WEBHOOK_ENCRYPTION_KEYS=$RBF_RESTORE_WEBHOOK_KEYS")
fi
log "Migriere und prüfe die Staging-Datenbank gegen den aktuellen Anwendungscode."
bw_compose run --rm --no-deps -T "${runtime_env_args[@]}" -e "DATABASE_URL=$staging_url" migrate
verify_database_schema_head "$staging_url"
report_check migration_and_schema_preflight passed "Alembic upgrade and exact head verification succeeded."

log "Prüfe verschlüsselte Anwendungsdaten mit dem aktuellen Schlüsselring."
bw_compose run --rm --no-deps -T "${runtime_env_args[@]}" -e "DATABASE_URL=$staging_url" migrate python -m app.db.restore_preflight \
  || die "Das Backup benötigt einen anderen WEBHOOK_ENCRYPTION_KEYS-Schlüsselring."
report_check secret_key_preflight passed "Encrypted application records are readable with the current key ring."

log "Starte das aktuelle API-Image isoliert gegen die Staging-Datenbank."
bw_compose run --rm --no-deps -T "${runtime_env_args[@]}" -e "DATABASE_URL=$staging_url" migrate sh -euc '
python -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000 >/tmp/rbf-preflight-api.log 2>&1 &
pid=$!
cleanup() { kill "$pid" >/dev/null 2>&1 || true; wait "$pid" >/dev/null 2>&1 || true; }
trap cleanup EXIT
for _ in $(seq 1 60); do
  if python -c "import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:8000/api/health/ready\", timeout=3)" >/dev/null 2>&1; then
    exit 0
  fi
  if ! kill -0 "$pid" >/dev/null 2>&1; then cat /tmp/rbf-preflight-api.log >&2; exit 1; fi
  sleep 2
done
cat /tmp/rbf-preflight-api.log >&2
exit 1
'
report_check application_readiness_preflight passed "Current API image reached readiness against the migrated staging database on the backend-only network."

if [[ "$preflight_only" == true ]]; then
  drop_database_if_exists "$staging_database"
  staging_created=false
  report_check preflight_cleanup passed "Temporary staging database was removed; active database was untouched."
  finish_report passed true
  restore_completed=true
  success "Recovery-Preflight bestanden; die aktive Datenbank wurde nicht verändert. Bericht: $report_path"
  exit 0
fi

log "Aktiviere den kurzen Wartungsmodus für den atomaren Datenbanktausch."
maintenance_enable restore 300
bw_compose stop api
maintenance_mode=true
postgres_admin -v target_db="$database" -v staging_db="$staging_database" -v rollback_db="$rollback_database" <<'SQL'
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE datname IN (:'target_db', :'staging_db', :'rollback_db') AND pid <> pg_backend_pid();
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'rollback_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'target_db', :'rollback_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'staging_db', :'target_db') \gexec
SQL
staging_created=false
swap_completed=true
report_check production_activation passed "Validated staging database was atomically activated while retaining rollback database."

bw_compose up -d --no-deps api
wait_for_api
bw_compose up -d --no-deps gateway
ensure_monitoring_services
maintenance_disable succeeded "Database restore completed successfully."
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
report_check production_smoke_test passed "Readiness and HTTPS smoke tests succeeded after activation."
drop_database_if_exists "$rollback_database"
maintenance_mode=false
swap_completed=false
restore_completed=true
report_check preflight_cleanup passed "Rollback database was removed after successful production validation."
finish_report passed true
success "PostgreSQL-Wiederherstellung validiert, atomar aktiviert und vollständig geprüft. Bericht: $report_path"
