#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[[ $# -eq 1 ]] || die "Aufruf: sudo $0 /pfad/backup.sql[.gz]"
[[ "$EUID" -eq 0 ]] || die "PostgreSQL-Restores benötigen root-Rechte. Verwende sudo $0 /pfad/backup.sql[.gz]."
require_command flock
backup_file="$(realpath "$1")"
[[ -f "$backup_file" ]] || die "Backup nicht gefunden: $backup_file"
verify_backup_checksum "$backup_file"
user="$(read_env POSTGRES_USER)"
database="$(read_env POSTGRES_DB)"
restore_lock="$INFRA_DIR/data/control/run/update.lock"
mkdir -p "$(dirname "$restore_lock")"
if [[ "${RBF_RESTORE_LOCK_HELD:-false}" != true ]]; then
  exec 9>"$restore_lock"
  flock -n 9 || die "Update, Restore oder eine andere exklusive Serveroperation läuft bereits."
fi

restore_completed=false
maintenance_mode=false
restore_on_exit() {
  local exit_code=$?
  if [[ "$restore_completed" != true && "$exit_code" -ne 0 ]]; then
    if [[ "$maintenance_mode" == true ]]; then
      ( bw_compose stop api gateway ) >/dev/null 2>&1 || true
      warn "PostgreSQL-Wiederherstellung fehlgeschlagen. API und Gateway bleiben zum Schutz vor Zugriffen auf einen möglicherweise inkonsistenten Datenstand gestoppt."
      warn "Vor dem nächsten Start Sicherheitsbackup und Datenbankzustand prüfen."
    else
      warn "PostgreSQL-Wiederherstellung wurde vor Aktivierung des Wartungsmodus abgebrochen; laufende Anwendungsdienste wurden nicht verändert."
    fi
  fi
}
trap restore_on_exit EXIT

warn "Die aktuelle Datenbank wird kontrolliert mit $backup_file überschrieben."
ensure_postgres_service
log "Erstelle vor dem Restore ein zusätzliches PostgreSQL-Sicherheitsbackup."
/usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-postgres.sh"

log "Aktiviere Wartungsmodus durch Stoppen von API und Gateway."
bw_compose stop api gateway
maintenance_mode=true

log "Beende verbleibende Verbindungen zur Zieldatenbank."
bw_compose exec -T postgres psql \
  -v ON_ERROR_STOP=1 \
  -v target_db="$database" \
  -U "$user" \
  -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :'target_db' AND pid <> pg_backend_pid();"

log "Spiele PostgreSQL-Backup in einer Transaktion ein."
if [[ "$backup_file" == *.gz ]]; then
  gzip -dc "$backup_file" | bw_compose exec -T postgres psql -1 -v ON_ERROR_STOP=1 -U "$user" "$database"
else
  bw_compose exec -T postgres psql -1 -v ON_ERROR_STOP=1 -U "$user" "$database" < "$backup_file"
fi

log "Bringe das wiederhergestellte Schema auf den Alembic-Head des aktuellen API-Images."
bw_compose run --rm migrate
verify_database_schema_head

log "Beende Wartungsmodus und starte die Anwendung kontrolliert."
bw_compose up -d --no-deps api
wait_for_api
bw_compose up -d --no-deps gateway
ensure_monitoring_services
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"

maintenance_mode=false
restore_completed=true
success "PostgreSQL-Wiederherstellung, Migration und Readiness-Prüfung abgeschlossen."
