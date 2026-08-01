#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"
require_command flock
run_dir="$INFRA_DIR/data/control/run"
install -d -m 0700 "$run_dir"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
health="$INFRA_DIR/data/control/status/backup-health.json"
install -d -m 0750 "$(dirname "$health")"
postgres_result="$(mktemp "$run_dir/postgres-result.XXXXXX")"
files_result="$(mktemp "$run_dir/files-result.XXXXXX")"
recovery_result="$(mktemp "$run_dir/recovery-result.XXXXXX")"
verification_result="$(mktemp "$run_dir/verification-result.XXXXXX")"
set_result="$(mktemp "$run_dir/set-result.XXXXXX")"
cleanup() { rm -f "$postgres_result" "$files_result" "$recovery_result" "$verification_result" "$set_result"; }
trap cleanup EXIT
python3 "$SCRIPT_DIR/backup_status.py" "$health" --status running --stage coordinating --reason scheduled --started-at "$started_at"
args=(--reason scheduled --postgres-result "$postgres_result" --files-result "$files_result" --recovery-result "$recovery_result" --verification-result "$verification_result" --backup-set-result "$set_result")
if is_true "$(read_env BACKUP_RECOVERY_ENABLED)"; then args+=(--include-recovery); fi
if ! /usr/bin/env bash "$SCRIPT_DIR/run-consistent-backup.sh" "${args[@]}"; then
  python3 "$SCRIPT_DIR/backup_status.py" "$health" --status failed --stage backup --reason scheduled --started-at "$started_at" --message "Coordinated backup or recovery verification failed."
  exit 1
fi
python3 "$SCRIPT_DIR/backup_status.py" "$health" --status succeeded --stage committed --reason scheduled --started-at "$started_at" \
  --postgres "$(cat "$postgres_result" 2>/dev/null || true)" \
  --files "$(cat "$files_result" 2>/dev/null || true)" \
  --recovery "$(cat "$recovery_result" 2>/dev/null || true)" \
  --verification "$(cat "$verification_result" 2>/dev/null || true)" \
  --backup-set "$(cat "$set_result" 2>/dev/null || true)" \
  --message "Backup set was committed only after a full recovery preflight."
