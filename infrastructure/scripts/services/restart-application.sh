#!/usr/bin/env bash
set -Eeuo pipefail
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/docker.sh"
source "$INFRA_DIR/scripts/lib/maintenance.sh"
[[ "$EUID" -eq 0 ]] || die "Der kontrollierte Anwendungsneustart benötigt root-Rechte."
maintenance_enable restart 60
trap 'code=$?; [[ $code -eq 0 ]] || maintenance_disable failed "Spring-Boot-Neustart fehlgeschlagen."' EXIT
bw_compose restart api
wait_for_api
maintenance_disable succeeded "Spring-Boot-Neustart abgeschlossen."
"$INFRA_DIR/scripts/checks/smoke-test.sh"
