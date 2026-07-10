#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

random_hex() {
  local bytes="${1:-24}"
  openssl rand -hex "$bytes"
}

escape_sed_value() {
  printf '%s' "$1" | sed -e 's/[&|]/\\&/g'
}

set_env_value() {
  local key="$1" value="$2" formatted escaped
  formatted="$value"
  if [[ "$value" =~ [[:space:]] ]]; then
    formatted="\"${value}\""
  fi
  escaped="$(escape_sed_value "$formatted")"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${escaped}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$formatted" >> "$ENV_FILE"
  fi
}

valid_ipv4() {
  [[ "$1" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]
}

detect_primary_ip() {
  local candidate
  candidate="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if valid_ipv4 "$candidate"; then
    printf '%s' "$candidate"
  else
    printf '127.0.0.1'
  fi
}

detect_app_hostname() {
  local short
  short="$(hostname -s 2>/dev/null || printf 'blackwater')"
  [[ -n "$short" ]] || short='blackwater'
  printf '%s.local' "$short"
}

initialize_env() {
  local requested_hostname="$1" requested_ip="$2" regenerate="$3" admin_username="$4" admin_display_name="$5"
  local created=false
  if [[ ! -f "$ENV_FILE" ]]; then
    cp "$INFRA_DIR/.env.example" "$ENV_FILE"
    created=true
  fi

  local app_hostname app_ip postgres_password admin_password secrets_changed=false
  app_hostname="${requested_hostname:-$(detect_app_hostname)}"
  app_ip="${requested_ip:-$(detect_primary_ip)}"

  if [[ "$created" == true || "$regenerate" == true || "$(read_env POSTGRES_PASSWORD)" == CHANGE_ME* ]]; then
    postgres_password="$(random_hex 24)"
    admin_password="$(random_hex 18)"
    set_env_value POSTGRES_PASSWORD "$postgres_password"
    set_env_value SEED_ADMIN_PASSWORD "$admin_password"
    secrets_changed=true
  else
    postgres_password="$(read_env POSTGRES_PASSWORD)"
    admin_password="$(read_env SEED_ADMIN_PASSWORD)"
  fi

  set_env_value APP_HOSTNAME "$app_hostname"
  set_env_value APP_IP "$app_ip"
  set_env_value POSTGRES_USER blackwater
  set_env_value POSTGRES_DB blackwater
  set_env_value DATABASE_URL "postgresql+psycopg://blackwater:${postgres_password}@postgres:5432/blackwater"
  set_env_value CORS_ORIGINS "https://${app_hostname},https://${app_ip}"
  set_env_value SEED_ADMIN_USERNAME "$admin_username"
  set_env_value SEED_ADMIN_DISPLAY_NAME "$admin_display_name"
  chmod 600 "$ENV_FILE"

  if [[ "$created" == true || "$regenerate" == true || "$secrets_changed" == true || ! -f "$INFRA_DIR/first-run-credentials.txt" ]]; then
    cat > "$INFRA_DIR/first-run-credentials.txt" <<CREDS
Blackwater Mercenaries Hub - First Run
URL: https://${app_ip}
Alternative URL: https://${app_hostname}
Admin user: ${admin_username}
Admin password: ${admin_password}
PostgreSQL user: blackwater
PostgreSQL password: ${postgres_password}

Protect this file and delete it after storing the credentials securely.
CREDS
    chmod 600 "$INFRA_DIR/first-run-credentials.txt"
  fi
}

validate_env() {
  local missing=()
  while IFS= read -r key; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    [[ -n "$(read_env "$key")" ]] || missing+=("$key")
  done < "$INFRA_DIR/config/env/required.env.keys"
  ((${#missing[@]} == 0)) || die "Fehlende .env-Werte: ${missing[*]}"
  [[ "$(read_env DB_SCHEMA_MODE)" == migrate ]] || die "Production benötigt DB_SCHEMA_MODE=migrate."
  [[ "$(read_env DATABASE_URL)" == postgresql+psycopg://* ]] || die "Production benötigt PostgreSQL."
}
