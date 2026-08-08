#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$(cd "$SCRIPT_DIR/../lib" && pwd)/docker.sh"
source "$SCRIPT_DIR/common.sh"

usage() {
  cat <<'USAGE'
Usage: sudo run-consistent-backup.sh [--reason TEXT] [--skip-postgres]
  [--include-recovery] [--lock-held|--all-locks-held]
  [--postgres-result FILE] [--files-result FILE] [--recovery-result FILE]
  [--verification-result FILE] [--backup-set-result FILE]
USAGE
}
reason="scheduled"
skip_postgres=false
include_recovery=false
lock_held=false
all_locks_held=false
postgres_result=""; files_result=""; recovery_result=""; verification_result=""; set_result=""
while (($#)); do
  case "$1" in
    --reason) reason="${2:-}"; shift 2 ;;
    --skip-postgres) skip_postgres=true; shift ;;
    --include-recovery) include_recovery=true; shift ;;
    --lock-held) lock_held=true; shift ;;
    --all-locks-held) lock_held=true; all_locks_held=true; shift ;;
    --postgres-result) postgres_result="${2:-}"; shift 2 ;;
    --files-result) files_result="${2:-}"; shift 2 ;;
    --recovery-result) recovery_result="${2:-}"; shift 2 ;;
    --verification-result) verification_result="${2:-}"; shift 2 ;;
    --backup-set-result) set_result="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown backup option: $1" ;;
  esac
done
[[ "$EUID" -eq 0 ]] || die "Coordinated backups require root privileges."
require_command flock
require_command python3
require_command sha256sum
run_dir="$INFRA_DIR/data/control/run"
install -d -m 0700 "$run_dir" "$INFRA_DIR/data/backups/reports" "$INFRA_DIR/data/backups/sets"
if [[ "$lock_held" != true && "${RBF_BACKUP_LOCK_HELD:-false}" != true ]]; then
  exec 9>"$run_dir/update.lock"; flock 9
fi
if [[ "$all_locks_held" != true && "${RBF_ALL_BACKUP_LOCKS_HELD:-false}" != true ]]; then
  exec 8>"$run_dir/backup.lock"; flock 8
fi


export_verified_recovery_set() {
  local recovery="$1" verification="$2" set_manifest="$3"
  local export_dir export_user export_group retention_days source target temporary
  export_dir="$(read_env BACKUP_PULL_EXPORT_DIR)"
  export_user="$(read_env BACKUP_PULL_EXPORT_USER)"
  [[ -n "$export_dir" || -n "$export_user" ]] || return 0
  [[ -n "$recovery" ]] || die "Pull export is configured, but no recovery bundle was created."
  [[ -n "$export_dir" && -n "$export_user" ]] || die "BACKUP_PULL_EXPORT_DIR and BACKUP_PULL_EXPORT_USER must be set together."
  [[ "$export_dir" == /* ]] || die "BACKUP_PULL_EXPORT_DIR must be absolute."
  id "$export_user" >/dev/null 2>&1 || die "BACKUP_PULL_EXPORT_USER does not exist: $export_user"
  export_group="$(id -gn "$export_user")"
  install -d -m 0700 -o "$export_user" -g "$export_group" "$export_dir"

  copy_atomic() {
    source="$1"
    [[ -f "$source" && ! -L "$source" ]] || die "Pull export source is missing or unsafe: $source"
    target="$export_dir/$(basename "$source")"
    temporary="$export_dir/.$(basename "$source").part.$$"
    rm -f "$temporary"
    install -m 0600 -o "$export_user" -g "$export_group" "$source" "$temporary"
    mv -f "$temporary" "$target"
  }

  copy_atomic "$recovery"
  copy_atomic "${recovery}.sha256"
  copy_atomic "$verification"
  copy_atomic "${verification}.sha256"
  copy_atomic "${set_manifest}.sha256"
  copy_atomic "$set_manifest"
  (
    cd "$export_dir"
    sha256sum -c "$(basename "${recovery}.sha256")" >/dev/null
    sha256sum -c "$(basename "${verification}.sha256")" >/dev/null
    sha256sum -c "$(basename "${set_manifest}.sha256")" >/dev/null
  )
  retention_days="$(read_env BACKUP_RETENTION_DAYS)"; retention_days="${retention_days:-14}"
  find "$export_dir" -maxdepth 1 -type f \
    \( -name 'rbf-recovery-*.tar.gz.age' -o -name 'rbf-recovery-*.tar.gz.age.sha256' \
       -o -name 'rbf-postgres-preflight-*.json' -o -name 'rbf-postgres-preflight-*.json.sha256' \
       -o -name 'rbf-backup-set-*.json' -o -name 'rbf-backup-set-*.json.sha256' \) \
    -mtime "+$retention_days" -delete
  success "Encrypted, recovery-verified pull export committed: $export_dir/$(basename "$set_manifest")"
}

own_postgres_result=false; own_files_result=false; own_recovery_result=false; own_verification_result=false; own_set_result=false
if [[ -z "$postgres_result" ]]; then postgres_result="$(mktemp "$run_dir/postgres-result.XXXXXX")"; own_postgres_result=true; fi
if [[ -z "$files_result" ]]; then files_result="$(mktemp "$run_dir/files-result.XXXXXX")"; own_files_result=true; fi
if [[ -z "$recovery_result" ]]; then recovery_result="$(mktemp "$run_dir/recovery-result.XXXXXX")"; own_recovery_result=true; fi
if [[ -z "$verification_result" ]]; then verification_result="$(mktemp "$run_dir/verification-result.XXXXXX")"; own_verification_result=true; fi
if [[ -z "$set_result" ]]; then set_result="$(mktemp "$run_dir/set-result.XXXXXX")"; own_set_result=true; fi

api_was_running=false
api_stopped=false
backup_completed=false
if bw_compose ps --status running -q api 2>/dev/null | grep -q .; then api_was_running=true; fi
quiesce="$(read_env BACKUP_QUIESCE_APPLICATION)"; quiesce="${quiesce:-true}"
consistency="no-running-api"
if [[ "$api_was_running" == true ]]; then
  if is_true "$quiesce"; then
    log "Briefly stop the API as the application-wide backup consistency boundary."
    bw_compose stop api
    api_stopped=true
    consistency="application-quiesced"
  else
    consistency="best-effort-live"
    die "Production backup rejected: BACKUP_QUIESCE_APPLICATION=false does not produce a verifiable recovery point."
  fi
fi

restore_api() {
  local exit_code=$?
  set +e
  if [[ "$api_stopped" == true ]]; then
    bw_compose up -d --no-deps api >/dev/null 2>&1 || true
    wait_for_api >/dev/null 2>&1 || true
    api_stopped=false
  fi
  if [[ "$backup_completed" != true ]]; then
    warn "Coordinated backup run was aborted; no backup-set commit was created."
  fi
  [[ "$own_postgres_result" == true ]] && rm -f "$postgres_result"
  [[ "$own_files_result" == true ]] && rm -f "$files_result"
  [[ "$own_recovery_result" == true ]] && rm -f "$recovery_result"
  [[ "$own_verification_result" == true ]] && rm -f "$verification_result"
  [[ "$own_set_result" == true ]] && rm -f "$set_result"
  exit "$exit_code"
}
trap restore_api EXIT

postgres_backup=""
if [[ "$skip_postgres" != true ]]; then
  BACKUP_REASON="$reason" BACKUP_CONSISTENCY_MODE="$consistency" BACKUP_RESULT_FILE="$postgres_result" \
    /usr/bin/env bash "$SCRIPT_DIR/backup-postgres.sh"
  postgres_backup="$(cat "$postgres_result")"
fi
BACKUP_RESULT_FILE="$files_result" /usr/bin/env bash "$SCRIPT_DIR/backup-data.sh"
files_backup="$(cat "$files_result")"

if [[ "$api_stopped" == true ]]; then
  bw_compose up -d --no-deps api
  wait_for_api
  api_stopped=false
fi

verification_report=""
if [[ -n "$postgres_backup" ]]; then
  verification_report="$INFRA_DIR/data/backups/reports/rbf-postgres-preflight-$(date -u +%Y%m%dT%H%M%SZ)-$$.json"
  RBF_RESTORE_LOCK_HELD=true /usr/bin/env bash "$SCRIPT_DIR/restore-postgres.sh" \
    --preflight-only --report "$verification_report" "$postgres_backup"
  printf '%s\n' "$verification_report" > "$verification_result"; chmod 600 "$verification_result"
fi

recovery_backup=""
if [[ "$include_recovery" == true ]]; then
  [[ -n "$postgres_backup" ]] || die "Recovery bundle requires a PostgreSQL backup."
  BACKUP_RESULT_FILE="$recovery_result" \
    /usr/bin/env bash "$SCRIPT_DIR/backup-recovery.sh" \
    --postgres "$postgres_backup" --files "$files_backup"
  recovery_backup="$(cat "$recovery_result")"
fi

set_path="$INFRA_DIR/data/backups/sets/rbf-backup-set-$(date -u +%Y%m%dT%H%M%SZ)-$$.json"
# In a versioned installation data/ is a symlink into the installation's shared
# tree. The helper verifies that relationship before widening the manifest root.
manifest_root="$(backup_manifest_root)"
manifest_args=(create --root "$manifest_root" --output "$set_path" --files "$files_backup" --reason "$reason")
[[ -z "$postgres_backup" ]] || manifest_args+=(--postgres "$postgres_backup" --verification "$verification_report")
[[ -z "$recovery_backup" ]] || manifest_args+=(--recovery "$recovery_backup")
python3 "$SCRIPT_DIR/backup_set_manifest.py" "${manifest_args[@]}" >/dev/null
backup_finalize "$set_path" "sets"
python3 "$SCRIPT_DIR/backup_set_manifest.py" validate --root "$manifest_root" "$set_path" >/dev/null
export_verified_recovery_set "$recovery_backup" "$verification_report" "$set_path"
printf '%s\n' "$set_path" > "$set_result"; chmod 600 "$set_result"
retention_days="$(read_env BACKUP_RETENTION_DAYS)"; retention_days="${retention_days:-14}"
find "$INFRA_DIR/data/backups/sets" -type f -mtime "+$retention_days" -delete
backup_completed=true
success "Coordinated and fully verified backup point created: $set_path"
