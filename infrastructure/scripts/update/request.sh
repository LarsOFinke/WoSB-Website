#!/usr/bin/env bash
set -Eeuo pipefail

update_apply_request_file() {
  [[ -f "$REQUEST_FILE" ]] || return 0

  local request_values=()
  mapfile -d '' -t request_values < <(
    json_read_fields "$REQUEST_FILE" requested_by operation requested_at
  )

  local requested_from_file="${request_values[0]:-}"
  local requested_operation="${request_values[1]:-}"
  local requested_at_from_file="${request_values[2]:-}"
  [[ -z "$requested_from_file" ]] || REQUESTED_BY="$requested_from_file"
  [[ -z "$requested_at_from_file" ]] || REQUESTED_AT="$requested_at_from_file"

  case "$requested_operation" in
    restart)
      RESTART_ONLY=true
      RUN_MIGRATIONS=false
      RUN_SEED=false
      RESTORE_SEED_DEFAULTS=false
      ;;
    ""|update)
      RESTART_ONLY=false
      RUN_MIGRATIONS=false
      RUN_SEED=false
      RESTORE_SEED_DEFAULTS=false
      ;;
    update_migrate)
      RESTART_ONLY=false
      RUN_MIGRATIONS=true
      RUN_SEED=false
      RESTORE_SEED_DEFAULTS=false
      ;;
    update_migrate_seed)
      RESTART_ONLY=false
      RUN_MIGRATIONS=true
      RUN_SEED=true
      RESTORE_SEED_DEFAULTS=false
      ;;
    update_migrate_seed_restore)
      RESTART_ONLY=false
      RUN_MIGRATIONS=true
      RUN_SEED=true
      RESTORE_SEED_DEFAULTS=true
      ;;
    *)
      RESTART_ONLY=false
      INVALID_REQUEST_OPERATION="$requested_operation"
      RUN_MIGRATIONS=false
      RUN_SEED=false
      ;;
  esac

  update_refresh_operation
  rm -f "$REQUEST_FILE"
}
