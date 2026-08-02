#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPDATE_DIR="$ROOT_DIR/infrastructure/scripts/update"

fail() {
  printf '[update-test] %s\n' "$*" >&2
  exit 1
}

(
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$UPDATE_DIR/options.sh"
  update_options_reset
  update_parse_options --seed
  [[ "$RUN_MIGRATIONS" == true ]] || fail "--seed must imply migrations"
  [[ "$RUN_SEED" == true ]] || fail "--seed must enable seed"
  [[ "$OPERATION" == update_migrate_seed ]] || fail "--seed operation must expose migrate+seed"
)

python3 - "$UPDATE_DIR/workflow.sh" <<'PY_RELOAD'
from pathlib import Path
import sys

workflow = Path(sys.argv[1]).read_text(encoding="utf-8")
run = workflow.split("update_run() {", 1)[1]
pull = run.index("update_repository")
reload = run.index('source "$UPDATE_LIB_DIR/workflow.sh"')
deploy = run.index("update_execute_deployment")
assert pull < reload < deploy, "fresh migration/deployment logic must be loaded after pull"
PY_RELOAD

(
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$ROOT_DIR/infrastructure/scripts/lib/json.sh"
  source "$UPDATE_DIR/options.sh"
  source "$UPDATE_DIR/request.sh"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  REQUEST_FILE="$tmp/restart.request"
  printf '{"requested_by":"admin","operation":"restart","requested_at":"2026-07-30T18:00:00+02:00"}\n' > "$REQUEST_FILE"
  update_options_reset
  update_apply_request_file
  [[ "$RESTART_ONLY" == true ]] || fail "restart request must enable restart-only mode"
  [[ "$RUN_MIGRATIONS" == false ]] || fail "restart request must not run migrations"
  [[ "$RUN_SEED" == false ]] || fail "restart request must not run seed"
  [[ "$OPERATION" == restart ]] || fail "restart request must expose restart operation"
)

(
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$UPDATE_DIR/options.sh"
  update_options_reset
  update_parse_options --restore-seed-defaults
  [[ "$RUN_MIGRATIONS" == true ]] || fail "--restore-seed-defaults must imply migrations"
  [[ "$RUN_SEED" == true ]] || fail "--restore-seed-defaults must enable seed"
  [[ "$RESTORE_SEED_DEFAULTS" == true ]] || fail "--restore-seed-defaults must release overrides"
  [[ "$OPERATION" == update_migrate_seed_restore ]] \
    || fail "restore operation must expose migrate+seed+restore"
)

(
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  mkdir -p "$tmp/site-packages"
  cp -a "$ROOT_DIR/backend/src/app" "$tmp/site-packages/app"
  cat > "$tmp/backend.env" <<ENV
APP_ENV=development
DATABASE_URL=sqlite:///$tmp/schema-head.db
DB_SCHEMA_MODE=none
UPLOAD_DIR=$tmp/uploads
CONTROL_DIR=$tmp/control
CORS_ORIGINS=http://localhost
SESSION_COOKIE_SECURE=false
AUTO_SEED=false
ENV
  (
    cd "$tmp"
    RBF_ENV_FILE="$tmp/backend.env" \
    RBF_CONFIG_DIR="$ROOT_DIR/backend/config" \
    RBF_ALEMBIC_CONFIG="$ROOT_DIR/backend/alembic.ini" \
    PYTHONPATH="$tmp/site-packages" \
      python3 - <<'PY_SCHEMA_HEAD'
from app.core.config import BACKEND_ROOT
from app.db.schema_health import expected_alembic_heads

assert not (BACKEND_ROOT / "alembic.ini").exists(), BACKEND_ROOT
assert expected_alembic_heads() == frozenset({"0023_build_printouts"})
PY_SCHEMA_HEAD
  )
)

(
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$UPDATE_DIR/workflow.sh"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  LOCK_FILE="$tmp/update.lock"
  INBOX_REQUEST_FILE="$tmp/update.request"
  printf '{}\n' > "$INBOX_REQUEST_FILE"
  warn() { :; }
  die() { return 1; }

  (
    exec 7>"$LOCK_FILE"
    flock 7
    sleep 3
  ) &
  holder=$!
  sleep 0.2
  LOCK_ACQUIRED=false
  UPDATE_LOCK_WAIT_SECONDS=1
  if update_acquire_lock; then
    fail "concurrent update unexpectedly acquired the lock"
  fi
  [[ -f "$INBOX_REQUEST_FILE" ]] || fail "busy updater consumed the pending request"
  [[ "$LOCK_ACQUIRED" == false ]] || fail "busy updater marked lock as acquired"
  wait "$holder"
)

(
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$UPDATE_DIR/workflow.sh"
  RUN_MIGRATIONS=false
  RUN_SEED=false
  AUTO_MIGRATIONS=true
  OPERATION=update
  SCHEMA_CURRENT_HEADS=pre_clean_schema
  SCHEMA_EXPECTED_HEADS=0001_baseline
  SCHEMA_MATCHES=false
  ensure_postgres_service() { :; }
  read_database_schema_state() { :; }
  update_refresh_operation() {
    if [[ "$RUN_MIGRATIONS" == true ]]; then OPERATION=update_migrate; fi
  }
  log() { :; }
  die() { return 1; }

  update_resolve_database_actions
  [[ "$RUN_MIGRATIONS" == true ]] || fail "pending database revisions were not detected"
  [[ "$OPERATION" == update_migrate ]] || fail "auto migration did not refresh operation"

  RUN_MIGRATIONS=false
  AUTO_MIGRATIONS=false
  OPERATION=update
  if update_resolve_database_actions; then
    fail "--no-auto-migrate allowed an incompatible deployment"
  fi
)

(
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$UPDATE_DIR/status.sh"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  STATUS_FILE="$tmp/update-status.json"
  STATUS_LOCK_FILE="$tmp/update-status.lock"
  OPERATION=update
  REQUESTED_BY=tester
  REQUESTED_AT=""
  HEARTBEAT_PID=""
  update_status_write running "test" "$(now_iso)"
  python3 - "$STATUS_FILE" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["state"] == "running"
assert payload["heartbeat_at"]
PY
  update_status_write succeeded "done" "$(now_iso)" "$(now_iso)"
  python3 - "$STATUS_FILE" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["state"] == "succeeded"
assert payload["heartbeat_at"] is None
PY
)


(
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  mkdir -p "$tmp/infrastructure/scripts/backup" "$tmp/control/run"
  cat > "$tmp/infrastructure/scripts/backup/run-consistent-backup.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s\n' "$*" > "$BACKUP_TEST_RESULT"
while (($#)); do
  case "$1" in
    --postgres-result|--files-result|--verification-result|--backup-set-result)
      printf '/tmp/test-artifact\n' > "$2"; shift 2 ;;
    --recovery-result) : > "$2"; shift 2 ;;
    *) shift ;;
  esac
done
SH
  chmod +x "$tmp/infrastructure/scripts/backup/run-consistent-backup.sh"
  cat > "$tmp/infrastructure/scripts/backup/sync-backup-set-remote.py" <<'PY'
from pathlib import Path
import os
Path(os.environ["SYNC_TEST_RESULT"]).write_text("called\n", encoding="utf-8")
PY

  if ! timeout 5 bash -c '
    set -Eeuo pipefail
    source "$1/infrastructure/scripts/lib/common.sh"
    source "$1/infrastructure/scripts/update/workflow.sh"
    INFRA_DIR="$2/infrastructure"
    RUN_DIR="$2/control/run"
    CREATE_BACKUP=true
    RUN_MIGRATIONS=true
    RUN_SEED=true
    BACKUP_TEST_RESULT="$2/result.txt"
    SYNC_TEST_RESULT="$2/sync-result.txt"
    export BACKUP_TEST_RESULT SYNC_TEST_RESULT
    log() { :; }
    exec 9>"$RUN_DIR/update.lock"
    flock 9
    update_create_backup
  ' _ "$ROOT_DIR" "$tmp"; then
    fail "database backup deadlocked while the updater already owned update.lock"
  fi
  grep -q -- '--lock-held --reason pre-update' "$tmp/result.txt" \
    || fail "database update did not invoke the coordinated runner with inherited update-lock semantics"
  [[ -f "$tmp/sync-result.txt" ]] \
    || fail "database update did not transfer the committed backup set to the configured remote target"
)

printf 'Update-management checks OK.\n'
