#!/usr/bin/env bash
set -Eeuo pipefail

update_options_reset() {
  REQUESTED_BY=manual
  REQUESTED_AT=""
  SKIP_PULL=false
  CREATE_BACKUP=true
  RUN_MIGRATIONS=false
  RUN_SEED=false
  RESTORE_SEED_DEFAULTS=false
  AUTO_MIGRATIONS=true
  OPERATION=update
  INVALID_REQUEST_OPERATION=""
}

update_usage() {
  cat <<'USAGE'
Usage: sudo ./update.sh [options]

Der Repository-Einstiegspunkt update.sh bleibt öffentlich und delegiert an
den Infrastruktur-Runner. Dieser Kommandozeilenvertrag bleibt stabil.

Default behavior updates API and frontend, compares the database revision with
the Alembic head in the newly built API image and automatically applies pending
migrations. PostgreSQL is never seeded unless explicitly requested.

Options:
  --migrate            Run Alembic migrations intentionally.
  --seed               Run migrations and then the idempotent seed intentionally.
  --restore-seed-defaults
                       Run migrations and seed after discarding overrides on
                       repository-owned master data. Custom records and user
                       content remain untouched.
  --no-auto-migrate    Refuse deployment when the database is behind instead of migrating.
  --requested-by NAME  Record the requesting operator.
  --skip-pull          Deploy the current checkout without fetching Git.
  --no-backup          Skip the pre-deployment file/database backup.
  -h, --help           Show this help.
USAGE
}

update_require_option_value() {
  local option="$1" value="${2:-}"
  [[ -n "$value" ]] || die "$option benötigt einen Wert."
}

update_parse_options() {
  while (($#)); do
    case "$1" in
      --requested-by) update_require_option_value "$1" "${2:-}"; REQUESTED_BY="$2"; shift 2 ;;
      --skip-pull) SKIP_PULL=true; shift ;;
      --no-backup) CREATE_BACKUP=false; shift ;;
      --migrate) RUN_MIGRATIONS=true; shift ;;
      --seed) RUN_MIGRATIONS=true; RUN_SEED=true; shift ;;
      --restore-seed-defaults)
        RUN_MIGRATIONS=true
        RUN_SEED=true
        RESTORE_SEED_DEFAULTS=true
        shift
        ;;
      --no-auto-migrate) AUTO_MIGRATIONS=false; shift ;;
      -h|--help) update_usage; exit 0 ;;
      *) die "Unbekannte Update-Option: $1" ;;
    esac
  done
  update_refresh_operation
}

update_refresh_operation() {
  if [[ "$RESTORE_SEED_DEFAULTS" == true ]]; then
    OPERATION=update_migrate_seed_restore
  elif [[ "$RUN_MIGRATIONS" == true && "$RUN_SEED" == true ]]; then
    OPERATION=update_migrate_seed
  elif [[ "$RUN_MIGRATIONS" == true ]]; then
    OPERATION=update_migrate
  else
    OPERATION=update
  fi
}
