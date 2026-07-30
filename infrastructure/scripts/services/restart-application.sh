#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/docker.sh"

[[ "$EUID" -eq 0 ]] || die "Der kontrollierte Anwendungsneustart benötigt root-Rechte."
require_command docker

log "Starte die FastAPI-Anwendung neu; PostgreSQL bleibt unverändert in Betrieb."
bw_compose restart api
wait_for_api

log "Starte das Frontend-Gateway neu."
bw_compose restart gateway

ensure_monitoring_services
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
success "API und Frontend-Gateway wurden kontrolliert neu gestartet."
