#!/usr/bin/env bash
set -Eeuo pipefail
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/docker.sh"
source "$INFRA_DIR/scripts/lib/maintenance.sh"
[[ "$EUID" -eq 0 ]] || die "The controlled application restart requires root privileges."
maintenance_enable restart 60
trap 'code=$?; [[ $code -eq 0 ]] || maintenance_disable failed "Spring Boot restart failed."' EXIT
bw_compose restart api
wait_for_api
"$INFRA_DIR/scripts/checks/smoke-test.sh"
maintenance_disable succeeded "Spring-Boot-Neustart abgeschlossen."
