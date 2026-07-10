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

while (($#)); do
  case "$1" in
    --requested-by) REQUESTED_BY="${2:-manual}"; shift 2 ;;
    --skip-pull) SKIP_PULL=true; shift ;;
    --no-backup) CREATE_BACKUP=false; shift ;;
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
        print(value or "")
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
else
  warn "Kein .git-Verzeichnis gefunden; Quellcode-Update wird übersprungen."
fi

if [[ "$CREATE_BACKUP" == true ]]; then
  log "Erstelle Sicherheitsbackup vor Deployment."
  /usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-all.sh"
fi

status_write running "Images werden gebaut und Datenbankmigrationen ausgeführt." "$STARTED_AT" "" "$COMMIT_BEFORE" "$COMMIT_AFTER"
bw_compose build --pull api gateway
deploy_stack
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"

FINISHED_AT="$(now_iso)"
status_write succeeded "Server-Update erfolgreich abgeschlossen." "$STARTED_AT" "$FINISHED_AT" "$COMMIT_BEFORE" "$COMMIT_AFTER"
UPDATE_COMPLETED=true
success "Server-Update erfolgreich abgeschlossen (${COMMIT_BEFORE:-unbekannt} → ${COMMIT_AFTER:-unbekannt})."
