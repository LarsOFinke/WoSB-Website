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
    *) die "Unknown option: $1" ;;
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
  echo "[smoke] Health check failed; latest container status:" >&2
  bw_compose_with_profiles ps >&2 || true
  echo "[smoke] Last API/gateway logs:" >&2
  bw_compose_with_profiles logs --tail=120 api gateway >&2 || true
  die "Health check failed. Logs: infrastructure/scripts/services/logs.sh api gateway"
fi
success "Gateway, Spring Boot, Flyway, and PostgreSQL are ready."

if [[ "$verify_bootstrap_login" == true ]]; then
  admin_username="$(read_env SEED_ADMIN_USERNAME)"
  admin_password="$(read_env SEED_ADMIN_PASSWORD)"
  [[ -n "$admin_username" && -n "$admin_password" && "$admin_password" != CHANGE_ME* ]] \
    || die "Bootstrap-admin credentials are missing for the first-run check."

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
    || die "Bootstrap-admin login could not be executed during the first-run smoke test."
  [[ "$login_status" == 200 ]] \
    || die "Bootstrap-admin login failed (HTTP ${login_status}); SEED_ADMIN_USERNAME/SEED_ADMIN_PASSWORD do not match the initialized user."
  success "Bootstrap-admin credentials were verified through the public login API."

  manageable_body="$(curl --fail "${base_args[@]}" --cookie "$cookie_jar" \
    "https://${hostname}/api/fleets/manageable")" \
    || die "Fleet-management preflight failed at /api/fleets/manageable."
  fleet_id="$(printf '%s' "$manageable_body" | grep -o '"id":[0-9][0-9]*' | head -n1 | cut -d: -f2 || true)"
  [[ -n "$fleet_id" ]] || die "Fleet-management preflight returned no manageable fleet."

  management_body="$(curl --fail "${base_args[@]}" --cookie "$cookie_jar" \
    "https://${hostname}/api/fleets/${fleet_id}/manage")" \
    || die "Fleet-management preflight failed at /api/fleets/${fleet_id}/manage."
  [[ "$management_body" == *'"memberships":'* && "$management_body" == *'"protected":'* ]] \
    || die "Fleet-management response does not match the expected DTO contract."

  curl --fail "${base_args[@]}" --cookie "$cookie_jar" \
    "https://${hostname}/api/fleets/${fleet_id}/roles?include_inactive=true" >/dev/null \
    || die "Fleet-management preflight failed while loading roles."
  success "Fleet-management API was verified end-to-end with the bootstrap administrator."
fi
