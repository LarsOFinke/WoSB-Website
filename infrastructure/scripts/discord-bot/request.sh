#!/usr/bin/env bash
set -Eeuo pipefail

discord_bot_load_request() {
  local request_values=()
  mapfile -d '' -t request_values < <(
    json_read_fields "$REQUEST_FILE" operation requested_by requested_at
  )

  OPERATION="${request_values[0]:-}"
  REQUESTED_BY="${request_values[1]:-}"
  REQUESTED_AT="${request_values[2]:-}"
}

discord_bot_operation_is_valid() {
  case "$1" in
    refresh|install|update|start|stop|restart|configure) return 0 ;;
    *) return 1 ;;
  esac
}
