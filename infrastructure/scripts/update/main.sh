#!/usr/bin/env bash
set -Eeuo pipefail

UPDATE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$UPDATE_LIB_DIR/../.." && pwd)"

source "$INFRA_DIR/scripts/lib/docker.sh"
source "$INFRA_DIR/scripts/lib/json.sh"
source "$UPDATE_LIB_DIR/options.sh"
source "$UPDATE_LIB_DIR/request.sh"
source "$UPDATE_LIB_DIR/status.sh"
source "$UPDATE_LIB_DIR/repository.sh"
source "$UPDATE_LIB_DIR/workflow.sh"

CONTROL_DIR="$INFRA_DIR/data/control"
REQUEST_FILE="$CONTROL_DIR/update.request"
STATUS_FILE="$CONTROL_DIR/update-status.json"
LOG_FILE="$CONTROL_DIR/update.log"
LOCK_FILE="$CONTROL_DIR/update.lock"

STARTED_AT=""
FINISHED_AT=""
COMMIT_BEFORE=""
COMMIT_AFTER=""
UPDATE_COMPLETED=false

update_main() {
  update_options_reset
  update_parse_options "$@"

  [[ "$EUID" -eq 0 ]] || die "Server-Updates benötigen root-Rechte. Verwende sudo ./update.sh."
  require_command flock
  require_command git
  require_command python3

  update_run
}
