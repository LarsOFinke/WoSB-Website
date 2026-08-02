#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"
ensure_env_file
require_command curl

force_insecure=false
if [[ "${1:-}" == "--insecure" ]]; then
  force_insecure=true
elif [[ -n "${1:-}" ]]; then
  die "Unbekannte Option für smoke-test.sh: $1"
fi

ip="$(read_env APP_IP)"
hostname="$(read_env APP_HOSTNAME)"
provider="$(read_env CERTIFICATE_PROVIDER)"
staging="$(read_env LETSENCRYPT_STAGING)"
url="https://${hostname}/api/health/ready"
curl_tls_args=()
if [[ "$force_insecure" == true || "$provider" != letsencrypt ]] || is_true "$staging"; then
  curl_tls_args+=(--insecure)
fi

health_file="$(mktemp)"
trap 'rm -f "$health_file"' EXIT

log "Warte auf die Anwendung unter $url"
for attempt in $(seq 1 60); do
  if curl --silent --show-error --fail "${curl_tls_args[@]}" --connect-timeout 3 --max-time 5 \
      --resolve "${hostname}:443:${ip}" "$url" >"$health_file" 2>/dev/null; then
    cat "$health_file"
    printf '\n'
    success "Gateway, API und Datenbank sind bereit."
    if is_true "$(read_env ENABLE_MONITORING)"; then
      monitoring_port="$(read_env MONITORING_HTTPS_PORT)"
      [[ "$monitoring_port" =~ ^[0-9]+$ ]] || monitoring_port=8443
      log "Warte auf Uptime Kuma unter https://${hostname}:${monitoring_port}"
      for _ in $(seq 1 60); do
        if curl --silent --show-error --fail "${curl_tls_args[@]}" --connect-timeout 3 --max-time 5 \
            --resolve "${hostname}:${monitoring_port}:${ip}" \
            "https://${hostname}:${monitoring_port}/" >/dev/null 2>&1; then
          success "Uptime Kuma ist über das Monitoring-Gateway erreichbar."
          exit 0
        fi
        sleep 2
      done
      die "Monitoring-Healthcheck ist fehlgeschlagen. Logs: infrastructure/scripts/services/logs.sh uptime-kuma monitoring-gateway"
    fi
    exit 0
  fi
  sleep 2
done

die "Healthcheck ist fehlgeschlagen. Logs: infrastructure/scripts/services/logs.sh api secure-api gateway"
