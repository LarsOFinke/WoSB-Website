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
assert expected_alembic_heads() == frozenset({"0005_webhook_security"})
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
  cat > "$tmp/infrastructure/scripts/backup/backup-postgres.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
printf 'postgres\n' >> "$BACKUP_TEST_RESULT"
SH
  cat > "$tmp/infrastructure/scripts/backup/backup-data.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
printf 'files\n' >> "$BACKUP_TEST_RESULT"
SH
  chmod +x "$tmp/infrastructure/scripts/backup/backup-postgres.sh" "$tmp/infrastructure/scripts/backup/backup-data.sh"

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
    export BACKUP_TEST_RESULT
    log() { :; }
    exec 9>"$RUN_DIR/update.lock"
    flock 9
    update_create_backup
  ' _ "$ROOT_DIR" "$tmp"; then
    fail "database backup deadlocked while the updater already owned update.lock"
  fi
  [[ "$(cat "$tmp/result.txt")" == $'postgres\nfiles' ]] \
    || fail "database update backup did not run PostgreSQL and file backup in order"
)


(
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  mkdir -p \
    "$tmp/infrastructure/scripts/backup" \
    "$tmp/infrastructure/scripts/lib" \
    "$tmp/infrastructure/data/control/run"
  cp "$ROOT_DIR/infrastructure/scripts/backup/backup-all.sh" \
    "$tmp/infrastructure/scripts/backup/backup-all.sh"
  cat > "$tmp/infrastructure/scripts/lib/common.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
require_command() { command -v "$1" >/dev/null 2>&1; }
SH
  cat > "$tmp/infrastructure/scripts/backup/backup-postgres.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
printf 'postgres\n' >> "$BACKUP_TEST_RESULT"
SH
  cat > "$tmp/infrastructure/scripts/backup/backup-data.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
printf 'files\n' >> "$BACKUP_TEST_RESULT"
SH
  chmod +x "$tmp/infrastructure/scripts/backup/"*.sh

  if ! timeout 5 bash -c '
    set -Eeuo pipefail
    BACKUP_TEST_RESULT="$1/result.txt"
    export BACKUP_TEST_RESULT
    exec 9>"$1/infrastructure/data/control/run/update.lock"
    flock 9
    /usr/bin/env bash "$1/infrastructure/scripts/backup/backup-all.sh"
  ' _ "$tmp"; then
    fail "backup-all did not reuse the inherited update lock during a self-update"
  fi
  [[ "$(cat "$tmp/result.txt")" == $'postgres\nfiles' ]] \
    || fail "self-update backup did not run PostgreSQL and file backup in order"
)

printf 'Update-management checks OK.\n'
