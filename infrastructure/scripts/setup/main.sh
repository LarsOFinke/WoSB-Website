#!/usr/bin/env bash
set -Eeuo pipefail

SETUP_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SETUP_LIB_DIR/../.." && pwd)"

source "$INFRA_DIR/scripts/lib/common.sh"
source "$INFRA_DIR/scripts/lib/env.sh"
source "$INFRA_DIR/scripts/lib/host.sh"
source "$INFRA_DIR/scripts/lib/docker.sh"
source "$SETUP_LIB_DIR/options.sh"
source "$SETUP_LIB_DIR/workflow.sh"

setup_main() {
  local entrypoint="$1"
  shift
  local original_args=("$@")

  setup_options_reset
  setup_parse_options "$@"
  setup_validate_options
  setup_require_root_if_needed "$entrypoint" "${original_args[@]}"
  setup_run
}
