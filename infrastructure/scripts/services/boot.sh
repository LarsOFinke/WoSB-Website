#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
# Images are built during setup/update. Boot runs the isolated schema boundary before the API.
deploy_stack
