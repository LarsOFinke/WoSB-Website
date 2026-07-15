#!/usr/bin/env bash
set -Eeuo pipefail

UPDATE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$UPDATE_LIB_DIR/../.." && pwd)"

source "$INFRA_DIR/scripts/lib/docker.sh"
source "$INFRA_DIR/scripts/lib/json.sh"
source "$INFRA_DIR/scripts/lib/host/control.sh"
source "$UPDATE_LIB_DIR/options.sh"
source "$UPDATE_LIB_DIR/request.sh"
source "$UPDATE_LIB_DIR/status.sh"
source "$UPDATE_LIB_DIR/repository.sh"
source "$UPDATE_LIB_DIR/workflow.sh"

CONTROL_ROOT="$INFRA_DIR/data/control"
INBOX_DIR="$CONTROL_ROOT/inbox"
STATUS_DIR="$CONTROL_ROOT/status"
RUN_DIR="$CONTROL_ROOT/run"
INBOX_REQUEST_FILE="$INBOX_DIR/update.request"
REQUEST_FILE="$RUN_DIR/update.request.$$"
STATUS_FILE="$STATUS_DIR/update-status.json"
LOG_FILE="$STATUS_DIR/update.log"
LOCK_FILE="$RUN_DIR/update.lock"
STATUS_LOCK_FILE="$RUN_DIR/update-status.lock"

STARTED_AT=""
FINISHED_AT=""
COMMIT_BEFORE=""
COMMIT_AFTER=""
UPDATE_COMPLETED=false
LOCK_ACQUIRED=false
HEARTBEAT_PID=""
API_IMAGE_BEFORE=""
API_IMAGE_TAG_BEFORE=""
GATEWAY_IMAGE_BEFORE=""
GATEWAY_IMAGE_TAG_BEFORE=""
SCHEMA_CURRENT_HEADS=""
SCHEMA_EXPECTED_HEADS=""
SCHEMA_MATCHES=false

update_main() {
  update_options_reset
  update_parse_options "$@"

  [[ "$EUID" -eq 0 ]] || die "Server-Updates benötigen root-Rechte. Verwende sudo ./update.sh."
  require_command flock
  require_command git
  require_command python3
  require_command docker

  update_run
}
