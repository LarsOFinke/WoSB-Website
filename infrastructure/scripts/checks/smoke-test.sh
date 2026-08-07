#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
ensure_env_file
require_command curl

force_insecure=false
verify_bootstrap_login=false
while (($#)); do
  case "$1" in
    --insecure) force_insecure=true ;;
    --bootstrap-login) verify_bootstrap_login=true ;;
    *) die "Unbekannte Option: $1" ;;
  esac
  shift
done

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '%s' "$value"
}

ip="$(read_env APP_IP)"
hostname="$(read_env APP_HOSTNAME)"
provider="$(read_env CERTIFICATE_PROVIDER)"
base_args=(--silent --show-error --connect-timeout 3 --max-time 8 --resolve "${hostname}:443:${ip}")
[[ "$force_insecure" == true || "$provider" != letsencrypt ]] && base_args+=(--insecure)

ready=false
for _ in $(seq 1 20); do
  if curl --fail "${base_args[@]}" "https://${hostname}/api/health/ready" >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done

if [[ "$ready" != true ]]; then
  echo "[smoke] Healthcheck fehlgeschlagen; letzter Containerstatus:" >&2
  bw_compose_with_profiles ps >&2 || true
  echo "[smoke] Letzte API-/Gateway-Logs:" >&2
  bw_compose_with_profiles logs --tail=120 api gateway >&2 || true
  die "Healthcheck ist fehlgeschlagen. Logs: infrastructure/scripts/services/logs.sh api gateway"
fi
success "Gateway, Spring Boot, Flyway und PostgreSQL sind bereit."

if [[ "$verify_bootstrap_login" == true ]]; then
  admin_username="$(read_env SEED_ADMIN_USERNAME)"
  admin_password="$(read_env SEED_ADMIN_PASSWORD)"
  [[ -n "$admin_username" && -n "$admin_password" && "$admin_password" != CHANGE_ME* ]] \
    || die "Bootstrap-Admin-Zugangsdaten fehlen für die First-Run-Prüfung."

  payload="{\"username\":\"$(json_escape "$admin_username")\",\"password\":\"$(json_escape "$admin_password")\"}"
  cookie_jar="$(mktemp)"
  trap 'rm -f "$cookie_jar"' EXIT
  login_status="$(curl "${base_args[@]}" \
    --header 'Content-Type: application/json' \
    --header "Origin: https://${hostname}" \
    --request POST \
    --data-binary "$payload" \
    --cookie-jar "$cookie_jar" \
    --output /dev/null \
    --write-out '%{http_code}' \
    "https://${hostname}/api/auth/login")" \
    || die "Bootstrap-Admin-Anmeldung konnte beim First-Run-Smoke-Test nicht ausgeführt werden."
  [[ "$login_status" == 200 ]] \
    || die "Bootstrap-Admin-Anmeldung ist fehlgeschlagen (HTTP ${login_status}); SEED_ADMIN_USERNAME/SEED_ADMIN_PASSWORD passen nicht zum initialisierten Benutzer."
  success "Bootstrap-Admin-Zugangsdaten wurden über die öffentliche Login-API verifiziert."

  manageable_body="$(curl --fail "${base_args[@]}" --cookie "$cookie_jar" \
    "https://${hostname}/api/fleets/manageable")" \
    || die "Fleet-Management-Preflight ist bei /api/fleets/manageable fehlgeschlagen."
  fleet_id="$(printf '%s' "$manageable_body" | grep -o '"id":[0-9][0-9]*' | head -n1 | cut -d: -f2 || true)"
  [[ -n "$fleet_id" ]] || die "Fleet-Management-Preflight hat keine verwaltbare Flotte geliefert."

  management_body="$(curl --fail "${base_args[@]}" --cookie "$cookie_jar" \
    "https://${hostname}/api/fleets/${fleet_id}/manage")" \
    || die "Fleet-Management-Preflight ist bei /api/fleets/${fleet_id}/manage fehlgeschlagen."
  [[ "$management_body" == *'"memberships":'* && "$management_body" == *'"protected":'* ]] \
    || die "Fleet-Management-Response entspricht nicht dem erwarteten DTO-Vertrag."

  curl --fail "${base_args[@]}" --cookie "$cookie_jar" \
    "https://${hostname}/api/fleets/${fleet_id}/roles?include_inactive=true" >/dev/null \
    || die "Fleet-Management-Preflight ist beim Laden der Rollen fehlgeschlagen."
  success "Fleet-Management-API wurde mit dem Bootstrap-Administrator end-to-end verifiziert."
fi
