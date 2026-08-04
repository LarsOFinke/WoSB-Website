#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$INFRA_DIR/scripts/lib/env.sh"
validate_env
bw_compose build api gateway
deploy_stack
