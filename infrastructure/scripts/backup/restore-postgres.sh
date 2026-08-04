#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/docker.sh"
source "$SCRIPT_DIR/common.sh"
source "$INFRA_DIR/scripts/lib/maintenance.sh"

usage() { echo "Usage: sudo restore-postgres.sh [--preflight-only] [--report FILE] BACKUP" >&2; exit 2; }
preflight_only=false; report=""
while (($#)); do
  case "$1" in
    --preflight-only) preflight_only=true; shift ;;
    --report) report="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    --*) usage ;;
    *) backup="${backup:-$1}"; shift ;;
  esac
done
[[ "$EUID" -eq 0 ]] || die "Restore benötigt root-Rechte."
[[ -n "${backup:-}" && -f "$backup" ]] || usage
require_command flock
verify_backup_checksum "$backup"
user="$(read_env POSTGRES_USER)"; database="$(read_env POSTGRES_DB)"
run_dir="$INFRA_DIR/data/control/run"; install -d -m 0700 "$run_dir"
exec 9>"$run_dir/update.lock"; flock 9
exec 8>"$run_dir/backup.lock"; flock 8
stamp="$(date -u +%Y%m%dT%H%M%SZ)-$$"
staging="rbf_restore_${stamp//[^0-9A-Za-z_]/_}"
rollback="rbf_rollback_${stamp//[^0-9A-Za-z_]/_}"
container="rbf-restore-preflight-${stamp,,}"
container="${container//_/-}"
report="${report:-$INFRA_DIR/data/backups/reports/rbf-restore-${stamp}.json}"
install -d -m 0700 "$(dirname "$report")"
cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  if [[ -n "${staging:-}" ]]; then
    bw_compose exec -T postgres psql -U "$user" -d postgres -v ON_ERROR_STOP=1 -c "drop database if exists \"$staging\" with (force)" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

bw_compose exec -T postgres pg_restore --list < "$backup" >/dev/null || die "Backup ist kein gültiger PostgreSQL-Custom-Dump."
ensure_postgres_service
bw_compose exec -T postgres psql -U "$user" -d postgres -v ON_ERROR_STOP=1 -c "create database \"$staging\" owner \"$user\" template template0"
bw_compose exec -T postgres pg_restore --exit-on-error --no-owner --no-privileges -U "$user" -d "$staging" < "$backup"

project="$(read_effective_env COMPOSE_PROJECT_NAME)"; image="$(read_effective_env RBF_API_IMAGE)"
[[ -n "$project" && -n "$image" ]] || die "Release-Umgebung enthält kein Compose-Projekt oder API-Image."
docker run -d --rm --name "$container" --network "${project}_backend" --env-file "$ENV_FILE" \
  -e "SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/$staging" \
  -e RBF_SCHEDULING_ENABLED=false -e CONTROL_DIR=/tmp/rbf-control \
  -v "$INFRA_DIR/data/uploads:/var/lib/rbf/uploads:ro" "$image" >/dev/null
ready=false
for _ in $(seq 1 90); do
  if docker exec "$container" wget -qO- http://127.0.0.1:8080/actuator/health/readiness >/dev/null 2>&1; then ready=true; break; fi
  docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null | grep -q true || break
  sleep 2
done
[[ "$ready" == true ]] || { docker logs "$container" >&2 || true; die "Restore-Preflight erreichte keine Spring-Boot-Readiness."; }
docker rm -f "$container" >/dev/null 2>&1 || true
flyway="$(bw_compose exec -T postgres psql -U "$user" -d "$staging" -Atqc "select coalesce(max(version),'') from flyway_schema_history where success")"
backup_sha="$(sha256sum "$backup" | awk '{print $1}')"
backup_size="$(stat -c %s "$backup")"
cat > "$report" <<JSON
{
  "schema_version": 2,
  "mode": "preflight",
  "status": "passed",
  "recoverable": true,
  "checked_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_artifact": {"filename":"$(basename "$backup")","size_bytes":$backup_size,"sha256":"$backup_sha"},
  "flyway_version": "$flyway",
  "application_version": "$(cat "$REPO_ROOT/VERSION")",
  "checks": [
    {"name":"dump_inventory","status":"passed"},
    {"name":"staging_database_restore","status":"passed"},
    {"name":"flyway_validation","status":"passed"},
    {"name":"application_readiness","status":"passed"},
    {"name":"preflight_cleanup","status":"passed"}
  ]
}
JSON
chmod 600 "$report"; backup_finalize "$report" reports
if [[ "$preflight_only" == true ]]; then success "Restore-Preflight bestanden: $report"; exit 0; fi

log "Erzeuge vor Aktivierung einen koordinierten Sicherheits-Backup-Punkt."
RBF_ALL_BACKUP_LOCKS_HELD=true "$SCRIPT_DIR/run-consistent-backup.sh" --all-locks-held --reason pre-restore
maintenance_enable restore 300
bw_compose stop api
bw_compose exec -T postgres psql -U "$user" -d postgres -v ON_ERROR_STOP=1 <<SQL
select pg_terminate_backend(pid) from pg_stat_activity where datname in ('$database','$staging','$rollback') and pid <> pg_backend_pid();
drop database if exists "$rollback" with (force);
alter database "$database" rename to "$rollback";
alter database "$staging" rename to "$database";
SQL
staging=""
if bw_compose up -d --no-deps api && wait_for_api && "$INFRA_DIR/scripts/checks/smoke-test.sh"; then
  bw_compose exec -T postgres psql -U "$user" -d postgres -v ON_ERROR_STOP=1 -c "drop database if exists \"$rollback\" with (force)"
  maintenance_disable succeeded "Datenbank-Restore erfolgreich."
  success "Validiertes Backup wurde atomar aktiviert."
else
  warn "Aktivierung fehlgeschlagen; stelle vorherige Datenbank wieder her."
  bw_compose stop api || true
  bw_compose exec -T postgres psql -U "$user" -d postgres -v ON_ERROR_STOP=1 <<SQL
select pg_terminate_backend(pid) from pg_stat_activity where datname in ('$database','$rollback') and pid <> pg_backend_pid();
drop database if exists "$database" with (force);
alter database "$rollback" rename to "$database";
SQL
  bw_compose up -d --no-deps api || true
  maintenance_disable failed "Restore fehlgeschlagen; Rollback aktiviert."
  die "Restore fehlgeschlagen; vorherige Datenbank wurde reaktiviert."
fi
