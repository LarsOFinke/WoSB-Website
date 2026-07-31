#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[[ $# -eq 1 ]] || die "Aufruf: sudo $0 /pfad/backup.sql[.gz]"
[[ "$EUID" -eq 0 ]] || die "PostgreSQL-Restores benötigen root-Rechte. Verwende sudo $0 /pfad/backup.sql[.gz]."
require_command flock
require_command python3
backup_file="$(realpath "$1")"
[[ -f "$backup_file" ]] || die "Backup nicht gefunden: $backup_file"
verify_backup_checksum "$backup_file"
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
staging_database="${database}_restore_${suffix}"
rollback_database="${database}_rollback_${suffix}"
failed_database="${database}_failed_${suffix}"
staging_database="${staging_database:0:63}"
rollback_database="${rollback_database:0:63}"
failed_database="${failed_database:0:63}"

restore_completed=false
maintenance_mode=false
swap_completed=false

url_for_database() {
  python3 - "$database_url" "$1" <<'PY'
from urllib.parse import urlsplit, urlunsplit
import sys
url, database = sys.argv[1:]
parts = urlsplit(url)
print(urlunsplit((parts.scheme, parts.netloc, f"/{database}", parts.query, parts.fragment)))
PY
}

postgres_admin() {
  bw_compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$user" -d postgres "$@"
}

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
  bw_compose stop api gateway >/dev/null 2>&1 || true
  postgres_admin \
    -v target_db="$database" \
    -v rollback_db="$rollback_database" \
    -v failed_db="$failed_database" <<'SQL'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname IN (:'target_db', :'rollback_db')
  AND pid <> pg_backend_pid();
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'failed_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'target_db', :'failed_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'rollback_db', :'target_db') \gexec
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'failed_db') \gexec
SQL
  swap_completed=false
  start_application_best_effort
}

restore_on_exit() {
  local exit_code=$?
  [[ "$restore_completed" == true || "$exit_code" -eq 0 ]] && return 0
  set +e
  if [[ "$swap_completed" == true ]]; then
    if rollback_database_swap; then
      warn "Restore fehlgeschlagen; die vorherige Datenbank wurde automatisch zurückgeschaltet und die Anwendung wieder gestartet."
    else
      warn "Automatischer Datenbank-Rollback ist fehlgeschlagen. API und Gateway bleiben zum Schutz gestoppt."
    fi
  elif [[ "$maintenance_mode" == true ]]; then
    if start_application_best_effort; then
      warn "Restore wurde vor dem Datenbanktausch abgebrochen; die unveränderte Anwendung wurde wieder gestartet."
    else
      warn "Restore wurde vor dem Datenbanktausch abgebrochen, aber die Anwendung konnte nicht automatisch wieder gestartet werden."
    fi
  else
    warn "PostgreSQL-Wiederherstellung wurde vor dem Wartungsmodus abgebrochen; laufende Anwendungsdienste wurden nicht verändert."
  fi
  drop_database_if_exists "$staging_database" >/dev/null 2>&1 || true
}
trap restore_on_exit EXIT

warn "Die aktuelle Datenbank wird kontrolliert mit $backup_file ersetzt."
ensure_postgres_service
log "Erstelle vor dem Restore ein zusätzliches PostgreSQL-Sicherheitsbackup."
/usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-postgres.sh"

log "Erzeuge eine isolierte Staging-Datenbank; die laufende Anwendung bleibt während Import und Prüfung erreichbar."
postgres_admin \
  -v staging_db="$staging_database" \
  -v database_owner="$user" <<'SQL'
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'staging_db') \gexec
SELECT format('CREATE DATABASE %I OWNER %I TEMPLATE template0', :'staging_db', :'database_owner') \gexec
SQL

log "Spiele PostgreSQL-Backup transaktional in die Staging-Datenbank ein."
if [[ "$backup_file" == *.gz ]]; then
  gzip -dc "$backup_file" | bw_compose exec -T postgres psql \
    -1 -v ON_ERROR_STOP=1 -U "$user" "$staging_database"
else
  bw_compose exec -T postgres psql \
    -1 -v ON_ERROR_STOP=1 -U "$user" "$staging_database" < "$backup_file"
fi

staging_url="$(url_for_database "$staging_database")"
log "Migriere und prüfe die Staging-Datenbank gegen den aktuellen Anwendungscode."
bw_compose run --rm --no-deps -e "DATABASE_URL=$staging_url" migrate
verify_database_schema_head "$staging_url"

log "Prüfe verschlüsselte Webhook- und Raid-Helper-Zugangsdaten mit dem aktuellen Schlüsselring."
if ! bw_compose run --rm --no-deps -T -e "DATABASE_URL=$staging_url" \
  migrate python -m app.db.restore_preflight; then
  die "Das Backup benötigt einen anderen WEBHOOK_ENCRYPTION_KEYS-Schlüsselring. Verwende das vollständige Recovery-Bundle oder stelle die alten Schlüssel vor dem Datenbank-Restore wieder her."
fi

log "Aktiviere den kurzen Wartungsmodus für den atomaren Datenbanktausch."
bw_compose stop api gateway
maintenance_mode=true

postgres_admin \
  -v target_db="$database" \
  -v staging_db="$staging_database" \
  -v rollback_db="$rollback_database" <<'SQL'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname IN (:'target_db', :'staging_db', :'rollback_db')
  AND pid <> pg_backend_pid();
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'rollback_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'target_db', :'rollback_db') \gexec
SELECT format('ALTER DATABASE %I RENAME TO %I', :'staging_db', :'target_db') \gexec
SQL
swap_completed=true

log "Starte Anwendung gegen die wiederhergestellte Datenbank und führe Readiness- sowie HTTPS-Smoke-Tests aus."
bw_compose up -d --no-deps api
wait_for_api
bw_compose up -d --no-deps gateway
ensure_monitoring_services
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"

log "Anwendungstest erfolgreich; entferne die nur für den automatischen Rollback gehaltene Alt-Datenbank."
drop_database_if_exists "$rollback_database"
maintenance_mode=false
swap_completed=false
restore_completed=true
success "PostgreSQL-Wiederherstellung wurde in einer Staging-Datenbank validiert, atomar aktiviert und vollständig geprüft."
