#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"
require_command flock

run_dir="$INFRA_DIR/data/control/run"
mkdir -p "$run_dir"
update_lock="$run_dir/update.lock"
expected_update_lock="$(realpath -m "$update_lock")"
inherited_update_lock=""
if [[ -e "/proc/$$/fd/9" ]]; then
  inherited_target="$(readlink -f "/proc/$$/fd/9" 2>/dev/null || true)"
  if [[ "$inherited_target" == "$expected_update_lock" ]] && flock -n 9; then
    inherited_update_lock=true
  fi
fi

if [[ "$inherited_update_lock" != true ]]; then
  exec 8>"$update_lock"
  flock 8
fi
exec 7>"$run_dir/backup.lock"
flock 7

postgres_result="$(mktemp "$run_dir/postgres-result.XXXXXX")"
files_result="$(mktemp "$run_dir/files-result.XXXXXX")"
cleanup() { rm -f "$postgres_result" "$files_result"; }
trap cleanup EXIT

BACKUP_RESULT_FILE="$postgres_result" /usr/bin/env bash "$SCRIPT_DIR/backup-postgres.sh"
BACKUP_RESULT_FILE="$files_result" /usr/bin/env bash "$SCRIPT_DIR/backup-data.sh"

recovery_enabled=false
if declare -F read_env >/dev/null 2>&1 && declare -F is_true >/dev/null 2>&1; then
  if is_true "$(read_env BACKUP_RECOVERY_ENABLED)"; then
    recovery_enabled=true
  fi
fi

if [[ "$recovery_enabled" == true ]]; then
  postgres_backup="$(cat "$postgres_result")"
  files_backup="$(cat "$files_result")"
  /usr/bin/env bash "$SCRIPT_DIR/backup-recovery.sh" \
    --postgres "$postgres_backup" \
    --files "$files_backup"
elif declare -F warn >/dev/null 2>&1; then
  warn "Verschlüsseltes Disaster-Recovery-Bundle ist deaktiviert (BACKUP_RECOVERY_ENABLED=false)."
fi
