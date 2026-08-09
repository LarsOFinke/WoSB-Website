#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

random_hex() {
  local bytes="${1:-24}"
  openssl rand -hex "$bytes"
}

random_fernet_key() {
  openssl rand -base64 32 | tr '+/' '-_' | tr -d '\n'
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

  local app_hostname app_ip postgres_user postgres_database postgres_password app_database_user app_database_password admin_password webhook_encryption_key secrets_changed=false
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
  app_database_user="$(read_env APP_DATABASE_USER)"
  [[ "$app_database_user" =~ ^[A-Za-z_][A-Za-z0-9_]{1,31}$ ]] || app_database_user=rbf_app
  if [[ "$created" == true || "$regenerate" == true || -z "$(read_env APP_DATABASE_PASSWORD)" || "$(read_env APP_DATABASE_PASSWORD)" == CHANGE_ME* ]]; then
    app_database_password="$(random_hex 24)"
    set_env_value APP_DATABASE_PASSWORD "$app_database_password"
    secrets_changed=true
  fi

  webhook_encryption_key="$(read_env WEBHOOK_ENCRYPTION_KEYS)"
  if [[ "$created" == true || "$regenerate" == true || -z "$webhook_encryption_key" || "$webhook_encryption_key" == CHANGE_ME* ]]; then
    webhook_encryption_key="$(random_fernet_key)"
    set_env_value WEBHOOK_ENCRYPTION_KEYS "$webhook_encryption_key"
    secrets_changed=true
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
  set_env_value CONTROL_DIR /var/lib/rbf/control
  [[ -n "$(read_env SESSION_COOKIE_NAME)" ]] || set_env_value SESSION_COOKIE_NAME rbf_hub_session
  [[ -n "$(read_env SESSION_COOKIE_SAMESITE)" ]] || set_env_value SESSION_COOKIE_SAMESITE Lax
  [[ -n "$(read_env SESSION_TTL_HOURS)" ]] || set_env_value SESSION_TTL_HOURS 24
  [[ -n "$(read_env COOKIE_CONSENT_RETENTION)" ]] || set_env_value COOKIE_CONSENT_RETENTION 400d
  [[ -n "$(read_env RESOLVED_PRIVACY_REQUEST_RETENTION)" ]] || set_env_value RESOLVED_PRIVACY_REQUEST_RETENTION 400d
  [[ -n "$(read_env PRIVACY_RETENTION_INTERVAL)" ]] || set_env_value PRIVACY_RETENTION_INTERVAL PT24H
  [[ -n "$(read_env GATEWAY_MAX_BODY_MB)" ]] || set_env_value GATEWAY_MAX_BODY_MB 90
  set_env_value POSTGRES_USER "$postgres_user"
  set_env_value POSTGRES_DB "$postgres_database"
  set_env_value APP_DATABASE_USER "$app_database_user"
  # Keep the canonical HTTPS origins and the local/IP fallbacks usable during
  # first-run setup and on test hosts without working DNS yet.
  set_env_value CORS_ORIGINS "https://${app_hostname},https://${app_ip},http://${app_hostname},http://${app_ip},http://localhost,http://127.0.0.1,https://localhost,https://127.0.0.1"
  set_env_value SEED_ADMIN_USERNAME "$admin_username"
  set_env_value SEED_ADMIN_DISPLAY_NAME "$admin_display_name"
  chmod 600 "$ENV_FILE"

  if [[ "$created" == true || "$regenerate" == true || "$secrets_changed" == true || ! -f "$INFRA_DIR/first-run-credentials.txt" ]]; then
    cat > "$INFRA_DIR/first-run-credentials.txt" <<CREDS
Royal Blackwater Fleet - First Run
Primary URL: https://${app_hostname}
LAN fallback: https://${app_ip}
Admin user: ${admin_username}
Admin password: ${admin_password}

Protect this file and delete it after storing the credentials securely.
CREDS
    chmod 600 "$INFRA_DIR/first-run-credentials.txt"
  fi
}

ensure_runtime_secrets() {
  ensure_env_file
  local webhook_encryption_key
  webhook_encryption_key="$(read_env WEBHOOK_ENCRYPTION_KEYS)"
  if [[ -z "$webhook_encryption_key" || "$webhook_encryption_key" == CHANGE_ME* ]]; then
    set_env_value WEBHOOK_ENCRYPTION_KEYS "$(random_fernet_key)"
    chmod 600 "$ENV_FILE"
    log "A separate key for encrypted Discord webhook credentials was generated."
  fi
  local app_database_user app_database_password
  app_database_user="$(read_env APP_DATABASE_USER)"
  [[ "$app_database_user" =~ ^[A-Za-z_][A-Za-z0-9_]{1,31}$ ]] || {
    app_database_user=rbf_app
    set_env_value APP_DATABASE_USER "$app_database_user"
  }
  app_database_password="$(read_env APP_DATABASE_PASSWORD)"
  if [[ -z "$app_database_password" || "$app_database_password" == CHANGE_ME* ]]; then
    set_env_value APP_DATABASE_PASSWORD "$(random_hex 24)"
    log "A separate restricted database runtime credential was generated."
  fi
  chmod 600 "$ENV_FILE"
}

validate_env() {
  local missing=()
  while IFS= read -r key; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    [[ -n "$(read_env "$key")" ]] || missing+=("$key")
  done < "$INFRA_DIR/config/env/required.env.keys"
  ((${#missing[@]} == 0)) || die "Missing .env values: ${missing[*]}"

  [[ "$(read_env POSTGRES_PASSWORD)" != CHANGE_ME* ]] || die "POSTGRES_PASSWORD was not generated."
  [[ "$(read_env APP_DATABASE_USER)" =~ ^[A-Za-z_][A-Za-z0-9_]{1,31}$ ]] || die "APP_DATABASE_USER is invalid."
  [[ -n "$(read_env APP_DATABASE_PASSWORD)" && "$(read_env APP_DATABASE_PASSWORD)" != CHANGE_ME* ]] || die "APP_DATABASE_PASSWORD was not generated."
  [[ "$(read_env WEBHOOK_ENCRYPTION_KEYS)" != CHANGE_ME* ]] || die "WEBHOOK_ENCRYPTION_KEYS was not generated."
  [[ "$(read_env FLYWAY_BASELINE_ON_MIGRATE)" =~ ^(true|false)$ ]] || die "FLYWAY_BASELINE_ON_MIGRATE must be true or false."
  [[ "$(read_env FLYWAY_BASELINE_ON_MIGRATE)" == false ]] || die "Production uses the verified cutover; baseline-on-migrate must remain false."
  [[ "$(read_env SESSION_COOKIE_SAMESITE)" =~ ^(Lax|Strict|None|lax|strict|none)$ ]] || die "SESSION_COOKIE_SAMESITE is invalid."
  [[ "$(read_env SESSION_TTL_HOURS)" =~ ^[1-9][0-9]*$ ]] || die "SESSION_TTL_HOURS must be a positive number."
  [[ "$(read_env GATEWAY_MAX_BODY_MB)" =~ ^[1-9][0-9]*$ ]] || die "GATEWAY_MAX_BODY_MB must be a positive number."

  local tls_mode certificate_provider hostname deployment_environment
  tls_mode="$(read_env TLS_MODE)"; certificate_provider="$(read_env CERTIFICATE_PROVIDER)"; hostname="$(read_env APP_HOSTNAME)"
  deployment_environment="$(read_env DEPLOYMENT_ENVIRONMENT)"
  [[ -z "$deployment_environment" || "$deployment_environment" =~ ^(test|production)$ ]] || die "DEPLOYMENT_ENVIRONMENT must be test or production."
  [[ "$tls_mode" =~ ^(auto|letsencrypt|self-signed)$ ]] || die "TLS_MODE must be auto, letsencrypt, or self-signed."
  [[ "$certificate_provider" =~ ^(self-signed|letsencrypt)$ ]] || die "CERTIFICATE_PROVIDER is invalid."
  [[ -n "$hostname" && "$hostname" != *" "* ]] || die "APP_HOSTNAME is invalid."
  if [[ "$tls_mode" == letsencrypt ]]; then
    [[ -n "$(read_env LETSENCRYPT_EMAIL)" ]] || die "TLS_MODE=letsencrypt requires LETSENCRYPT_EMAIL."
    [[ "$hostname" != *.local && ! "$hostname" =~ ^[0-9.]+$ ]] || die "Let's Encrypt requires a public domain name."
  fi
  [[ "$(read_env LETSENCRYPT_STAGING)" =~ ^(true|false)$ ]] || die "LETSENCRYPT_STAGING must be true or false."
  if [[ "$deployment_environment" == production ]]; then
    [[ "$tls_mode" == letsencrypt ]] || die "Production requires TLS_MODE=letsencrypt; auto/self-signed is not allowed there."
    [[ "$(read_env LETSENCRYPT_STAGING)" == false ]] || die "Production must never use Let's Encrypt staging."
    [[ "$hostname" == *.* && "$hostname" != *.local && ! "$hostname" =~ ^[0-9.]+$ ]] || die "Production requires a public TLS hostname."
  fi
  local retention="$(read_env BACKUP_RETENTION_DAYS)"
  [[ -z "$retention" || "$retention" =~ ^[1-9][0-9]*$ ]] || die "BACKUP_RETENTION_DAYS must be positive."
}
