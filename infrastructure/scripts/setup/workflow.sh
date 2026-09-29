#!/usr/bin/env bash
set -Eeuo pipefail

migrate_legacy_runtime_names() {
  [[ -f "$ENV_FILE" ]] || return 0

  local legacy_project
  legacy_project="$(read_env COMPOSE_PROJECT_NAME)"
  [[ "$legacy_project" == rbv-hub || "$legacy_project" == blackwater-hub ]] || return 0

  log "Migrating the former Docker project name ${legacy_project} to rbf-hub."
  if command -v docker >/dev/null 2>&1 && compose_binary >/dev/null 2>&1; then
    bw_compose_with_profiles down --remove-orphans \
      || warn "The old stack could not be stopped completely; setup will continue the migration."
  fi
  set_env_value COMPOSE_PROJECT_NAME rbf-hub
}

setup_prepare_host() {
  if [[ "$SKIP_HOST" == false ]]; then
    install_host_dependencies
    if [[ -n "$SSH_ADMIN_PUBLIC_KEY_FILE" ]]; then
      /usr/bin/env bash "$SETUP_LIB_DIR/provision-ssh-admin.sh" \
        "$SSH_ADMIN_USERNAME" "$SSH_ADMIN_PUBLIC_KEY_FILE"
    else
      warn "No SSH public key provided; the separate SSH admin will not be configured."
    fi
    return
  fi

  require_command docker
  compose_binary >/dev/null || die "Docker Compose is missing."
  require_command openssl
}

setup_prepare_configuration() {
  if [[ ! -f "$INFRA_DIR/data/postgres/PG_VERSION" ]]; then
    VERIFY_BOOTSTRAP_LOGIN=true
  fi
  if [[ "$REGENERATE_SECRETS" == true && -f "$INFRA_DIR/data/postgres/PG_VERSION" ]]; then
    die "--regenerate-secrets is allowed only before the first PostgreSQL initialization. Use the documented secret rotation for existing installations."
  fi

  migrate_legacy_runtime_names
  initialize_env \
    "$REQUESTED_HOSTNAME" \
    "$REQUESTED_IP" \
    "$REGENERATE_SECRETS" \
    "$ADMIN_USERNAME" \
    "$ADMIN_DISPLAY_NAME" \
    "${REQUESTED_LETSENCRYPT_EMAIL:-}"

  validate_env
}

setup_prepare_runtime() {
  prepare_data_directories

  if [[ "$SKIP_HOST" == false && "$CONFIGURE_FIREWALL" == true ]]; then
    configure_firewall
  fi

  if [[ "$SKIP_HOST" == false && "$INSTALL_SYSTEMD" == true ]]; then
    /usr/bin/env bash "$INFRA_DIR/scripts/deployment/install-systemd.sh"
  fi

  if [[ "$SKIP_HOST" == false ]]; then
    /usr/bin/env bash "$INFRA_DIR/scripts/checks/host-security.sh"
  fi

  bw_compose_with_profiles config >/dev/null
  success "Compose configuration is valid."
}

setup_deploy() {
  if [[ "$NO_START" == true ]]; then
    warn "Container startup was skipped with --no-start."
    return
  fi

  bw_compose_with_profiles pull postgres
  bw_compose build api gateway
  deploy_stack
  configure_host_nginx
  smoke_args=()
  [[ "$VERIFY_BOOTSTRAP_LOGIN" == true ]] && smoke_args+=(--bootstrap-login)
  /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh" "${smoke_args[@]}"
}

setup_print_summary() {
  local app_hostname
  app_hostname="$(read_env APP_HOSTNAME)"
  cat <<SUMMARY

============================================================
 Royal Blackwater Fleet is configured
============================================================
 Fleet Hub:       $([[ "$(read_env DEPLOYMENT_ENVIRONMENT)" == production ]] && echo https || echo http)://${app_hostname}
 API readiness:  $([[ "$(read_env DEPLOYMENT_ENVIRONMENT)" == production ]] && echo https || echo http)://${app_hostname}/api/health/ready
 PostgreSQL:      localhost:$(read_env POSTGRES_LOCAL_PORT) (loopback only)
 Monitoring:      removed (Uptime Kuma)
 Host gateway:    /etc/nginx/sites-available/$(read_env APP_HOSTNAME).conf (or preserved legacy site)
 Credentials:     $INFRA_DIR/first-run-credentials.txt
 SSH administration: $([[ -n "$SSH_ADMIN_PUBLIC_KEY_FILE" ]] && echo "$SSH_ADMIN_USERNAME (publickey)" || echo "not configured")

 Host NGINX owns ports 80 and 443. The project gateway is private on
 127.0.0.1:$(read_env RBF_LOOPBACK_PORT).

 Verbleibende Administrator-Gates:
 - Complete the first login and securely remove bootstrap credentials
 - Legally review and publish the legal notice and privacy policy
 - Independently verify DNS, public TLS, and externally reachable ports
 - Test SSH key access; only then disable password/root login
 - Enroll the backup system and record a complete restore test
============================================================
SUMMARY
}

setup_run() {
  log "Preparing RBF first-run setup."
  "$INFRA_DIR/scripts/checks/preflight.sh" setup
  log "Profile: $PROFILE | Host provisioning: $([[ "$SKIP_HOST" == true ]] && echo off || echo on)"

  setup_prepare_host
  setup_prepare_configuration
  setup_prepare_runtime
  setup_deploy
  setup_print_summary
}
