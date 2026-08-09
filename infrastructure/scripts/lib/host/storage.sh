#!/usr/bin/env bash
set -Eeuo pipefail

prepare_data_directories() {
  mkdir -p "$INFRA_DIR/data"/{postgres,uploads,nginx,certs,backups,acme,control/inbox,control/status,control/run,control/secrets,recovered-config,runtime-secrets,letsencrypt/config,letsencrypt/work,letsencrypt/logs}
  prepare_postgres_directory
  apply_runtime_ownership
  apply_runtime_permissions
  materialize_runtime_secrets
}

prepare_postgres_directory() {
  rm -f "$INFRA_DIR/data/postgres/.gitkeep"

  if [[ ! -f "$INFRA_DIR/data/postgres/PG_VERSION" ]]; then
    local unexpected_entry=""
    unexpected_entry="$(find "$INFRA_DIR/data/postgres" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)"
    [[ -z "$unexpected_entry" ]] \
      || die "PostgreSQL data directory is not empty before initialization: $unexpected_entry"
  fi
}

apply_runtime_ownership() {
  [[ "$EUID" -eq 0 ]] || return 0

  chown -R 70:70 "$INFRA_DIR/data/postgres"
  chown -R 10001:10001 "$INFRA_DIR/data/uploads"
  chown root:10001 "$INFRA_DIR/data/control"
  chown -R 10001:10001 "$INFRA_DIR/data/control/inbox"
  chown -R root:10001 "$INFRA_DIR/data/control/status"
  chown -R root:root "$INFRA_DIR/data/control/run" "$INFRA_DIR/data/control/secrets" "$INFRA_DIR/data/recovered-config"
  chown -R root:root "$INFRA_DIR/data/runtime-secrets"
  chown -R 101:101 "$INFRA_DIR/data/nginx"
}

apply_runtime_permissions() {
  chmod 750 "$INFRA_DIR/data/postgres" "$INFRA_DIR/data/uploads" "$INFRA_DIR/data/backups"
  chmod 750 "$INFRA_DIR/data/control"
  chmod 700 "$INFRA_DIR/data/control/inbox" "$INFRA_DIR/data/control/run" "$INFRA_DIR/data/control/secrets" "$INFRA_DIR/data/recovered-config"
  chmod 700 "$INFRA_DIR/data/runtime-secrets"
  chmod 755 "$INFRA_DIR/data/control/status"
  chmod 755 "$INFRA_DIR/data/acme" "$INFRA_DIR/data/certs"
  chmod 700 \
    "$INFRA_DIR/data/letsencrypt" \
    "$INFRA_DIR/data/letsencrypt/config" \
    "$INFRA_DIR/data/letsencrypt/work" \
    "$INFRA_DIR/data/letsencrypt/logs"
}

materialize_runtime_secrets() {
  [[ "$EUID" -eq 0 ]] || die "Runtime secret materialization requires root privileges."
  local secrets="$INFRA_DIR/data/runtime-secrets"
  install -d -m 0700 -o root -g root "$secrets"
  install_secret() {
    local name="$1" value="$2" group="$3"
    local temporary="$secrets/.${name}.tmp.$$"
    umask 077
    printf '%s' "$value" > "$temporary"
    chown root:"$group" "$temporary"
    chmod 0440 "$temporary"
    mv -f "$temporary" "$secrets/$name"
  }
  install_secret postgres-owner-password "$(read_env POSTGRES_PASSWORD)" 70
  install_secret schema-owner-password "$(read_env POSTGRES_PASSWORD)" 10001
  install_secret schema-app-password "$(read_env APP_DATABASE_PASSWORD)" 10001
  install_secret api-app-password "$(read_env APP_DATABASE_PASSWORD)" 10001
  install_secret api-encryption-keys "$(read_env WEBHOOK_ENCRYPTION_KEYS)" 10001
  install_secret api-bootstrap-password "$(read_env SEED_ADMIN_PASSWORD)" 10001
}
