#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
ensure_env_file
require_command curl
force_insecure=false
[[ "${1:-}" == --insecure ]] && force_insecure=true || [[ -z "${1:-}" ]] || die "Unbekannte Option: $1"
ip="$(read_env APP_IP)"; hostname="$(read_env APP_HOSTNAME)"; provider="$(read_env CERTIFICATE_PROVIDER)"
args=(--silent --show-error --fail --connect-timeout 3 --max-time 8 --resolve "${hostname}:443:${ip}")
[[ "$force_insecure" == true || "$provider" != letsencrypt ]] && args+=(--insecure)
for _ in $(seq 1 20); do
  if curl "${args[@]}" "https://${hostname}/api/health/ready" >/dev/null 2>&1; then
    success "Gateway, Spring Boot, Flyway und PostgreSQL sind bereit."
    exit 0
  fi
  sleep 2
done
echo "[smoke] Healthcheck fehlgeschlagen; letzter Containerstatus:" >&2
bw_compose_with_profiles ps >&2 || true
echo "[smoke] Letzte API-/Gateway-Logs:" >&2
bw_compose_with_profiles logs --tail=120 api gateway >&2 || true
die "Healthcheck ist fehlgeschlagen. Logs: infrastructure/scripts/services/logs.sh api gateway"
