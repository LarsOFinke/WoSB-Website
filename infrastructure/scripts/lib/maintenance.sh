#!/usr/bin/env bash

maintenance_status_dir() {
  printf '%s/data/control/status' "$INFRA_DIR"
}

maintenance_control() {
  local action="$1"
  shift
  PYTHONPATH="$REPO_ROOT/backend/src" python3 -m app.cli.maintenance_mode \
    "$action" --status-dir "$(maintenance_status_dir)" "$@"
}

maintenance_enable() {
  local reason="$1" retry_after="${2:-120}"
  maintenance_control enable --reason "$reason" --retry-after "$retry_after"
  MAINTENANCE_ACTIVE=true
}

maintenance_disable() {
  maintenance_control disable || rm -f "$(maintenance_status_dir)/maintenance-mode.json"
  MAINTENANCE_ACTIVE=false
}
