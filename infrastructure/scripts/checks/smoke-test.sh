#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"
ensure_env_file
require_command curl

ip="$(read_env APP_IP)"
hostname="$(read_env APP_HOSTNAME)"
url="https://${ip}/api/health/ready"

log "Warte auf die Anwendung unter $url"
for attempt in $(seq 1 60); do
  if curl --silent --show-error --fail --insecure --connect-timeout 3 --max-time 5 \
      --resolve "${hostname}:443:${ip}" "https://${hostname}/api/health/ready" >/tmp/blackwater-health.json 2>/dev/null; then
    cat /tmp/blackwater-health.json
    printf '\n'
    rm -f /tmp/blackwater-health.json
    success "Gateway, API und Datenbank sind bereit."
    exit 0
  fi
  sleep 2
done

die "Healthcheck ist fehlgeschlagen. Logs: infrastructure/scripts/services/logs.sh api gateway"
