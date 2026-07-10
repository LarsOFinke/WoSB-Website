#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"

[[ "$EUID" -eq 0 ]] || die "Server-Updates benötigen root-Rechte. Verwende sudo ./update.sh."
require_command flock
require_command git
require_command python3

CONTROL_DIR="$INFRA_DIR/data/control"
REQUEST_FILE="$CONTROL_DIR/update.request"
STATUS_FILE="$CONTROL_DIR/update-status.json"
LOG_FILE="$CONTROL_DIR/update.log"
LOCK_FILE="$CONTROL_DIR/update.lock"
REQUESTED_BY="manual"
SKIP_PULL=false
CREATE_BACKUP=true
RUN_MIGRATIONS=false
RUN_SEED=false
AUTO_MIGRATIONS=true

usage() {
  cat <<'USAGE'
Usage: sudo ./update.sh [options]

Default behavior updates only the API and frontend gateway. PostgreSQL is not
started, recreated, migrated or seeded unless a database action is explicitly
required.

Options:
  --migrate            Run Alembic migrations intentionally.
  --seed               Run the idempotent seed intentionally.
  --no-auto-migrate    Do not auto-run migrations when new migration files are pulled.
  --requested-by NAME  Record the requesting operator.
  --skip-pull          Deploy the current checkout without fetching Git.
  --no-backup          Skip the pre-deployment file/database backup.
  -h, --help           Show this help.
USAGE
}

while (($#)); do
  case "$1" in
    --requested-by) REQUESTED_BY="${2:-manual}"; shift 2 ;;
    --skip-pull) SKIP_PULL=true; shift ;;
    --no-backup) CREATE_BACKUP=false; shift ;;
    --migrate) RUN_MIGRATIONS=true; shift ;;
    --seed) RUN_SEED=true; shift ;;
    --no-auto-migrate) AUTO_MIGRATIONS=false; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unbekannte Update-Option: $1" ;;
  esac
done

mkdir -p "$CONTROL_DIR"
chmod 770 "$CONTROL_DIR"
touch "$LOG_FILE"
chmod 664 "$LOG_FILE"

read_request_value() {
  local key="$1"
  python3 - "$REQUEST_FILE" "$key" <<'PY' 2>/dev/null || true
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
key = sys.argv[2]
if path.is_file():
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get(key, "")
        print(value if value is not None else "")
    except Exception:
        pass
PY
}

if [[ -f "$REQUEST_FILE" ]]; then
  requested_from_file="$(read_request_value requested_by)"
  [[ -z "$requested_from_file" ]] || REQUESTED_BY="$requested_from_file"
fi
rm -f "$REQUEST_FILE"

status_write() {
  local state="$1" message="$2" started_at="${3:-}" finished_at="${4:-}" before="${5:-}" after="${6:-}"
  STATE="$state" MESSAGE="$message" REQUESTED_BY="$REQUESTED_BY" STARTED_AT="$started_at" FINISHED_AT="$finished_at" COMMIT_BEFORE="$before" COMMIT_AFTER="$after" STATUS_FILE="$STATUS_FILE" python3 <<'PY'
import json, os
from datetime import datetime, timezone
from pathlib import Path
path = Path(os.environ["STATUS_FILE"])
old = {}
try:
    old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
except Exception:
    old = {}
requested_at = old.get("requested_at") or datetime.now(timezone.utc).isoformat()
payload = {
    "state": os.environ["STATE"],
    "message": os.environ["MESSAGE"],
    "requested_by": os.environ.get("REQUESTED_BY") or old.get("requested_by"),
    "requested_at": requested_at,
    "started_at": os.environ.get("STARTED_AT") or old.get("started_at"),
    "finished_at": os.environ.get("FINISHED_AT") or None,
    "commit_before": os.environ.get("COMMIT_BEFORE") or old.get("commit_before"),
    "commit_after": os.environ.get("COMMIT_AFTER") or old.get("commit_after"),
}
tmp = path.with_name(f".{path.name}.tmp")
tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
tmp.replace(path)
path.chmod(0o664)
PY
}

now_iso() { date --iso-8601=seconds; }

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  status_write failed "Ein anderes Server-Update läuft bereits." "" "$(now_iso)"
  die "Ein anderes Server-Update läuft bereits."
fi

STARTED_AT="$(now_iso)"
COMMIT_BEFORE=""
COMMIT_AFTER=""
status_write running "Server-Update wird vorbereitet." "$STARTED_AT"

# Keep a complete host-side transcript for the Staff Panel while still writing
# to the terminal during manual updates.
exec > >(tee -a "$LOG_FILE") 2>&1

UPDATE_COMPLETED=false
on_exit() {
  local exit_code=$?
  if [[ "$UPDATE_COMPLETED" != true && "$exit_code" -ne 0 ]]; then
    local finished
    finished="$(now_iso)"
    status_write failed "Server-Update fehlgeschlagen (Exit ${exit_code})." "$STARTED_AT" "$finished" "$COMMIT_BEFORE" "$COMMIT_AFTER" || true
    warn "Server-Update fehlgeschlagen. Details: $LOG_FILE"
  fi
}
trap on_exit EXIT

repo_owner() {
  stat -c '%U' "$REPO_ROOT" 2>/dev/null || printf 'root'
}

git_as_owner() {
  local owner
  owner="$(repo_owner)"
  if [[ "$owner" != root && "$owner" != UNKNOWN && -n "$owner" ]] && command -v runuser >/dev/null 2>&1; then
    runuser -u "$owner" -- git -C "$REPO_ROOT" "$@"
  else
    git -c safe.directory="$REPO_ROOT" -C "$REPO_ROOT" "$@"
  fi
}

migration_files_changed() {
  [[ -n "$COMMIT_BEFORE" && -n "$COMMIT_AFTER" && "$COMMIT_BEFORE" != "$COMMIT_AFTER" ]] || return 1
  [[ -n "$(git_as_owner diff --name-only "$COMMIT_BEFORE..$COMMIT_AFTER" -- backend/migrations/versions 2>/dev/null)" ]]
}

database_action_summary() {
  local actions=()
  [[ "$RUN_MIGRATIONS" == true ]] && actions+=("Migrationen")
  [[ "$RUN_SEED" == true ]] && actions+=("Seed")
  if ((${#actions[@]} == 0)); then
    printf 'keine; PostgreSQL bleibt unverändert'
  else
    local joined
    joined="$(IFS=', '; echo "${actions[*]}")"
    printf '%s' "$joined"
  fi
}

log "Server-Update angefordert von: $REQUESTED_BY"

if [[ -d "$REPO_ROOT/.git" ]]; then
  git_as_owner config core.fileMode false
  COMMIT_BEFORE="$(git_as_owner rev-parse --short HEAD)"
  dirty="$(git_as_owner status --porcelain --untracked-files=no)"
  [[ -z "$dirty" ]] || die "Repository enthält lokale Änderungen. Update abgebrochen, um Datenverlust zu vermeiden."

  if [[ "$SKIP_PULL" == false ]]; then
    log "Repository wird per fast-forward aktualisiert."
    git_as_owner fetch --prune origin
    git_as_owner pull --ff-only
  else
    log "Git-Pull wurde per --skip-pull übersprungen."
  fi
  COMMIT_AFTER="$(git_as_owner rev-parse --short HEAD)"

  if [[ "$AUTO_MIGRATIONS" == true && "$RUN_MIGRATIONS" == false ]] && migration_files_changed; then
    RUN_MIGRATIONS=true
    log "Neue Alembic-Migrationsdateien erkannt; Migrationen werden beabsichtigt ausgeführt."
  fi
else
  warn "Kein .git-Verzeichnis gefunden; Quellcode-Update und automatische Migrationserkennung werden übersprungen."
fi

log "Datenbankaktionen: $(database_action_summary)."

if [[ "$CREATE_BACKUP" == true ]]; then
  if [[ "$RUN_MIGRATIONS" == true || "$RUN_SEED" == true ]]; then
    log "Erstelle Sicherheitsbackup inklusive PostgreSQL vor beabsichtigten Datenbankarbeiten."
    /usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-all.sh"
  else
    log "Erstelle Datei-Backup; PostgreSQL wird für dieses Code-Update nicht angesprochen."
    /usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-data.sh"
  fi
fi

# Monitoring is independent from the application deployment. Bring an existing
# stack back first, then refresh its gateway again after the image build.
ensure_monitoring_services

status_write running "API und Frontend werden gebaut. Datenbankaktionen: $(database_action_summary)." "$STARTED_AT" "" "$COMMIT_BEFORE" "$COMMIT_AFTER"
bw_compose build --pull api gateway

# Ensure the monitoring gateway now uses the freshly built NGINX image before
# any optional database action can fail the deployment.
ensure_monitoring_services

deploy_application_update "$RUN_MIGRATIONS" "$RUN_SEED"
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"

FINISHED_AT="$(now_iso)"
status_write succeeded "Server-Update erfolgreich abgeschlossen. Datenbankaktionen: $(database_action_summary)." "$STARTED_AT" "$FINISHED_AT" "$COMMIT_BEFORE" "$COMMIT_AFTER"
UPDATE_COMPLETED=true
success "Server-Update erfolgreich abgeschlossen (${COMMIT_BEFORE:-unbekannt} → ${COMMIT_AFTER:-unbekannt})."
