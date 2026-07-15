#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[[ $# -eq 1 ]] || die "Aufruf: $0 /pfad/backup.sql[.gz]"
backup_file="$(realpath "$1")"
[[ -f "$backup_file" ]] || die "Backup nicht gefunden: $backup_file"
verify_backup_checksum "$backup_file"
user="$(read_env POSTGRES_USER)"
database="$(read_env POSTGRES_DB)"

warn "Die aktuelle Datenbank wird mit $backup_file überschrieben."
if [[ "$backup_file" == *.gz ]]; then
  gzip -dc "$backup_file" | bw_compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$user" "$database"
else
  bw_compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$user" "$database" < "$backup_file"
fi
success "PostgreSQL-Wiederherstellung abgeschlossen."
