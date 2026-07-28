#!/usr/bin/env bash
set -Eeuo pipefail

prepare_data_directories() {
  mkdir -p "$INFRA_DIR/data"/{postgres,uploads,nginx,certs,backups,uptime-kuma,acme,control/inbox,control/status,control/run,control/secrets,letsencrypt/config,letsencrypt/work,letsencrypt/logs}
  prepare_postgres_directory
  apply_runtime_ownership
  apply_runtime_permissions
}

prepare_postgres_directory() {
  rm -f "$INFRA_DIR/data/postgres/.gitkeep"

  if [[ ! -f "$INFRA_DIR/data/postgres/PG_VERSION" ]]; then
    local unexpected_entry=""
    unexpected_entry="$(find "$INFRA_DIR/data/postgres" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)"
    [[ -z "$unexpected_entry" ]] \
      || die "PostgreSQL-Datenverzeichnis ist vor der Initialisierung nicht leer: $unexpected_entry"
  fi
}

apply_runtime_ownership() {
  [[ "$EUID" -eq 0 ]] || return 0

  chown -R 70:70 "$INFRA_DIR/data/postgres"
  chown -R 10001:10001 "$INFRA_DIR/data/uploads"
  chown -R 10001:10001 "$INFRA_DIR/data/control/inbox"
  chown -R root:root "$INFRA_DIR/data/control/status" "$INFRA_DIR/data/control/run" "$INFRA_DIR/data/control/secrets"
  chown -R 101:101 "$INFRA_DIR/data/nginx"
  chown -R 1000:1000 "$INFRA_DIR/data/uptime-kuma"
}

apply_runtime_permissions() {
  chmod 750 "$INFRA_DIR/data/postgres" "$INFRA_DIR/data/uploads" "$INFRA_DIR/data/backups"
  chmod 750 "$INFRA_DIR/data/control"
  chmod 700 "$INFRA_DIR/data/control/inbox" "$INFRA_DIR/data/control/run" "$INFRA_DIR/data/control/secrets"
  chmod 755 "$INFRA_DIR/data/control/status"
  chmod 755 "$INFRA_DIR/data/acme" "$INFRA_DIR/data/certs"
  chmod 700 \
    "$INFRA_DIR/data/letsencrypt" \
    "$INFRA_DIR/data/letsencrypt/config" \
    "$INFRA_DIR/data/letsencrypt/work" \
    "$INFRA_DIR/data/letsencrypt/logs"
}
