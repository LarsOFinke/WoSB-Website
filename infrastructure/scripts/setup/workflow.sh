#!/usr/bin/env bash
set -Eeuo pipefail

migrate_legacy_runtime_names() {
  [[ -f "$ENV_FILE" ]] || return 0

  local legacy_project
  legacy_project="$(read_env COMPOSE_PROJECT_NAME)"
  [[ "$legacy_project" == rbv-hub || "$legacy_project" == blackwater-hub ]] || return 0

  log "Migriere den früheren Docker-Projektnamen ${legacy_project} auf rbf-hub."
  if command -v docker >/dev/null 2>&1 && compose_binary >/dev/null 2>&1; then
    bw_compose_with_profiles down --remove-orphans \
      || warn "Der alte Stack konnte nicht vollständig gestoppt werden; Setup setzt die Migration fort."
  fi
  set_env_value COMPOSE_PROJECT_NAME rbf-hub
}

setup_prepare_host() {
  if [[ "$SKIP_HOST" == false ]]; then
    install_host_dependencies
    return
  fi

  require_command docker
  compose_binary >/dev/null || die "Docker Compose fehlt."
  require_command openssl
}

setup_prepare_configuration() {
  if [[ "$REGENERATE_SECRETS" == true && -f "$INFRA_DIR/data/postgres/PG_VERSION" ]]; then
    die "--regenerate-secrets ist nur vor der ersten PostgreSQL-Initialisierung erlaubt. Nutze für bestehende Installationen die dokumentierte Secret-Rotation."
  fi

  migrate_legacy_runtime_names
  initialize_env \
    "$REQUESTED_HOSTNAME" \
    "$REQUESTED_IP" \
    "$REGENERATE_SECRETS" \
    "$ADMIN_USERNAME" \
    "$ADMIN_DISPLAY_NAME" \
    "$REQUESTED_TLS_MODE" \
    "$REQUESTED_LETSENCRYPT_EMAIL" \
    "$REQUESTED_LETSENCRYPT_STAGING"

  if [[ "$PROFILE" == full ]]; then
    set_env_value ENABLE_MONITORING true
  else
    set_env_value ENABLE_MONITORING false
  fi
  validate_env
}

setup_prepare_runtime() {
  if [[ "$REGENERATE_SECRETS" == true ]]; then
    rm -f "$INFRA_DIR/data/certs/fullchain.pem" "$INFRA_DIR/data/certs/privkey.pem"
  fi

  prepare_data_directories
  generate_self_signed_certificate

  if [[ "$SKIP_HOST" == false && "$CONFIGURE_FIREWALL" == true ]]; then
    configure_firewall
  fi

  if [[ "$SKIP_HOST" == false && "$INSTALL_SYSTEMD" == true ]]; then
    /usr/bin/env bash "$INFRA_DIR/scripts/deployment/install-systemd.sh"
  fi

  bw_compose_with_profiles config >/dev/null
  success "Compose-Konfiguration ist gültig."
}

setup_deploy() {
  if [[ "$NO_START" == true ]]; then
    warn "Containerstart wurde mit --no-start übersprungen."
    return
  fi

  bw_compose_with_profiles pull postgres
  if [[ "$PROFILE" == full ]]; then
    bw_compose_with_profiles pull uptime-kuma
  fi
  bw_compose build api gateway
  deploy_stack
  /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh" --insecure
  configure_production_tls
  /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
}

setup_print_summary() {
  local app_ip app_hostname monitoring
  app_ip="$(read_env APP_IP)"
  app_hostname="$(read_env APP_HOSTNAME)"
  if [[ "$PROFILE" == full ]]; then
    monitoring="https://${app_hostname}:$(read_env MONITORING_HTTPS_PORT)"
  else
    monitoring="deaktiviert"
  fi

  cat <<SUMMARY

============================================================
 Royal Blackwater Fleet ist eingerichtet
============================================================
 Fleet Hub:       https://${app_hostname}
 LAN fallback:    https://${app_ip}
 API readiness:  https://${app_hostname}/api/health/ready
 PostgreSQL:      localhost:$(read_env POSTGRES_LOCAL_PORT) (nur Loopback)
 Monitoring:      ${monitoring}
 TLS provider:    $(read_env CERTIFICATE_PROVIDER)
 Credentials:     $INFRA_DIR/first-run-credentials.txt

 Für Let's Encrypt müssen DNS sowie TCP-Port 80 und 443 auf diesen Pi zeigen.
 Ohne erfolgreiche Domainvalidierung bleibt das Bootstrap-Zertifikat aktiv.
============================================================
SUMMARY
}

setup_run() {
  log "RBF First-Run Setup wird vorbereitet."
  "$INFRA_DIR/scripts/checks/preflight.sh" setup
  log "Profil: $PROFILE | Host-Provisioning: $([[ "$SKIP_HOST" == true ]] && echo aus || echo an)"

  setup_prepare_host
  setup_prepare_configuration
  setup_prepare_runtime
  setup_deploy
  setup_print_summary
}
