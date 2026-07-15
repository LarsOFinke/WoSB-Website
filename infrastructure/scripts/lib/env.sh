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
  short="$(hostname -s 2>/dev/null || printf 'rbf')"
  [[ -n "$short" ]] || short='rbf'
  printf '%s.local' "$short"
}

initialize_env() {
  local requested_hostname="$1" requested_ip="$2" regenerate="$3" admin_username="$4" admin_display_name="$5"
  local requested_tls_mode="${6:-}" requested_letsencrypt_email="${7:-}" requested_staging="${8:-}"
  local created=false
  if [[ ! -f "$ENV_FILE" ]]; then
    cp "$INFRA_DIR/.env.example" "$ENV_FILE"
    created=true
  fi

  local app_hostname app_ip postgres_user postgres_database postgres_password admin_password secrets_changed=false
  if [[ -n "$requested_hostname" ]]; then
    app_hostname="$requested_hostname"
  elif [[ "$created" == true ]]; then
    app_hostname="$(read_env APP_HOSTNAME)"
    [[ -n "$app_hostname" ]] || app_hostname="$(detect_app_hostname)"
  else
    app_hostname="$(read_env APP_HOSTNAME)"
    [[ -n "$app_hostname" ]] || app_hostname="$(detect_app_hostname)"
  fi
  app_ip="${requested_ip:-$(detect_primary_ip)}"

  postgres_user="$(read_env POSTGRES_USER)"
  postgres_database="$(read_env POSTGRES_DB)"
  [[ -n "$postgres_user" && "$postgres_user" != CHANGE_ME* ]] || postgres_user=rbf
  [[ -n "$postgres_database" && "$postgres_database" != CHANGE_ME* ]] || postgres_database=rbf

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

  local tls_mode letsencrypt_email
  tls_mode="${requested_tls_mode:-$(read_env TLS_MODE)}"
  [[ -n "$tls_mode" ]] || tls_mode=auto
  letsencrypt_email="${requested_letsencrypt_email:-$(read_env LETSENCRYPT_EMAIL)}"

  set_env_value APP_HOSTNAME "$app_hostname"
  set_env_value APP_IP "$app_ip"
  set_env_value TLS_MODE "$tls_mode"
  set_env_value LETSENCRYPT_EMAIL "$letsencrypt_email"
  local letsencrypt_staging
  letsencrypt_staging="${requested_staging:-$(read_env LETSENCRYPT_STAGING)}"
  [[ -n "$letsencrypt_staging" ]] || letsencrypt_staging=false
  set_env_value LETSENCRYPT_STAGING "$letsencrypt_staging"
  local certificate_name="$app_hostname"
  is_true "$letsencrypt_staging" && certificate_name="${app_hostname}-staging"
  set_env_value LETSENCRYPT_CERT_NAME "$certificate_name"
  [[ -n "$(read_env CERTIFICATE_PROVIDER)" ]] || set_env_value CERTIFICATE_PROVIDER self-signed
  [[ -n "$(read_env MONITORING_HTTPS_PORT)" ]] || set_env_value MONITORING_HTTPS_PORT 8443
  set_env_value CONTROL_REQUEST_DIR /run/rbf-control/inbox
  set_env_value CONTROL_STATUS_DIR /run/rbf-control/status
  set_env_value POSTGRES_USER "$postgres_user"
  set_env_value POSTGRES_DB "$postgres_database"
  set_env_value DATABASE_URL "postgresql+psycopg://${postgres_user}:${postgres_password}@postgres:5432/${postgres_database}"
  set_env_value CORS_ORIGINS "https://${app_hostname},https://${app_ip}"
  set_env_value SEED_ADMIN_USERNAME "$admin_username"
  set_env_value SEED_ADMIN_DISPLAY_NAME "$admin_display_name"
  chmod 600 "$ENV_FILE"

  if [[ "$created" == true || "$regenerate" == true || "$secrets_changed" == true || ! -f "$INFRA_DIR/first-run-credentials.txt" ]]; then
    cat > "$INFRA_DIR/first-run-credentials.txt" <<CREDS
Royal Blackwater Fleet - First Run
Primary URL: https://${app_hostname}
LAN fallback: https://${app_ip}
Monitoring: https://${app_hostname}:$(read_env MONITORING_HTTPS_PORT)
Admin user: ${admin_username}
Admin password: ${admin_password}
PostgreSQL user: ${postgres_user}
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

  local postgres_user postgres_password postgres_database expected_database_url
  postgres_user="$(read_env POSTGRES_USER)"
  postgres_password="$(read_env POSTGRES_PASSWORD)"
  postgres_database="$(read_env POSTGRES_DB)"
  expected_database_url="postgresql+psycopg://${postgres_user}:${postgres_password}@postgres:5432/${postgres_database}"
  [[ "$(read_env DATABASE_URL)" == "$expected_database_url" ]] || \
    die "DATABASE_URL und POSTGRES_* Zugangsdaten sind nicht konsistent."

  local tls_mode certificate_provider hostname
  tls_mode="$(read_env TLS_MODE)"
  certificate_provider="$(read_env CERTIFICATE_PROVIDER)"
  hostname="$(read_env APP_HOSTNAME)"
  [[ "$tls_mode" =~ ^(auto|letsencrypt|self-signed)$ ]] || die "TLS_MODE muss auto, letsencrypt oder self-signed sein."
  [[ "$certificate_provider" =~ ^(self-signed|letsencrypt)$ ]] || die "CERTIFICATE_PROVIDER ist ungültig."
  [[ -n "$hostname" && "$hostname" != *" "* ]] || die "APP_HOSTNAME ist ungültig."
  if [[ "$tls_mode" == letsencrypt ]]; then
    [[ -n "$(read_env LETSENCRYPT_EMAIL)" ]] || die "TLS_MODE=letsencrypt benötigt LETSENCRYPT_EMAIL oder --letsencrypt-email."
    [[ "$hostname" != *.local && ! "$hostname" =~ ^[0-9.]+$ ]] || die "Let's Encrypt benötigt einen öffentlich auflösbaren Domainnamen."
  fi
  [[ "$(read_env LETSENCRYPT_STAGING)" =~ ^(true|false)$ ]] || die "LETSENCRYPT_STAGING muss true oder false sein."
  [[ "$(read_env MONITORING_HTTPS_PORT)" =~ ^[0-9]+$ ]] || die "MONITORING_HTTPS_PORT muss numerisch sein."
}
