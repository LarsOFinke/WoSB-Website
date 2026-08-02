#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/docker.sh"
source "$INFRA_DIR/scripts/lib/maintenance.sh"

MAINTENANCE_ACTIVE=false
cleanup_maintenance() {
  local exit_code=$?
  [[ "$MAINTENANCE_ACTIVE" != true ]] || maintenance_disable
  exit "$exit_code"
}
trap cleanup_maintenance EXIT

[[ "$EUID" -eq 0 ]] || die "Der kontrollierte Anwendungsneustart benötigt root-Rechte."
require_command docker

log "Starte die FastAPI-Anwendung neu; PostgreSQL bleibt unverändert in Betrieb."
maintenance_enable restart 60
bw_compose restart api
wait_for_api
ensure_monitoring_services
maintenance_disable
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
success "API und Frontend-Gateway wurden kontrolliert neu gestartet."
