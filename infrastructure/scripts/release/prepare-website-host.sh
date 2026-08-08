#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"
source "$INFRA_DIR/scripts/lib/host/packages.sh"

[[ "$EUID" -eq 0 ]] || die "Host preparation requires root privileges."
install_host_dependencies
