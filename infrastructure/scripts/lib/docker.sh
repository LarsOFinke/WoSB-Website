#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose_binary() {
  if docker compose version >/dev/null 2>&1; then
    printf 'docker compose'
  elif command -v docker-compose >/dev/null 2>&1; then
    printf 'docker-compose'
  else
    return 1
  fi
}

bw_compose() {
  ensure_env_file
  local compose
  compose="$(compose_binary)" || die "Docker Compose wurde nicht gefunden."
  # Runtime credentials must always come from infrastructure/.env. Shell-level
  # variables would otherwise take precedence during Compose interpolation and
  # could initialize PostgreSQL with a different password than the API receives.
  (
    cd "$INFRA_DIR"
    env \
      -u POSTGRES_USER \
      -u POSTGRES_PASSWORD \
      -u POSTGRES_DB \
      -u DATABASE_URL \
      $compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  )
}

compose_profiles() {
  if is_true "$(read_env ENABLE_MONITORING)"; then
    printf '%s\n' '--profile' 'monitoring'
  fi
}

bw_compose_with_profiles() {
  local args=()
  while IFS= read -r line; do [[ -n "$line" ]] && args+=("$line"); done < <(compose_profiles)
  bw_compose "${args[@]}" "$@"
}

wait_for_postgres() {
  local user database
  user="$(read_env POSTGRES_USER)"
  database="$(read_env POSTGRES_DB)"
  log "Warte auf PostgreSQL."
  for _ in $(seq 1 60); do
    if bw_compose exec -T postgres pg_isready -U "$user" -d "$database" >/dev/null 2>&1; then
      success "PostgreSQL ist bereit."
      return 0
    fi
    sleep 2
  done
  die "PostgreSQL wurde nicht rechtzeitig bereit. Logs: infrastructure/scripts/services/logs.sh postgres"
}

wait_for_api() {
  log "Warte auf die API-Readiness."
  for _ in $(seq 1 60); do
    if bw_compose exec -T api python -c \
      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=4)" \
      >/dev/null 2>&1; then
      success "API und Datenbank sind bereit."
      return 0
    fi
    sleep 2
  done
  die "API wurde nicht rechtzeitig bereit. Logs: infrastructure/scripts/services/logs.sh api"
}

ensure_monitoring_services() {
  ensure_env_file
  if ! is_true "$(read_env ENABLE_MONITORING)"; then
    log "Monitoring ist deaktiviert; Uptime Kuma wird nicht gestartet."
    return 0
  fi

  log "Stelle Uptime Kuma und das HTTPS-Monitoring-Gateway sicher."
  bw_compose_with_profiles up -d --no-deps uptime-kuma monitoring-gateway
}

deploy_application_update() {
  local run_migrations="${1:-false}"
  local run_seed="${2:-false}"

  ensure_env_file

  if [[ "$run_migrations" == true || "$run_seed" == true ]]; then
    log "Stelle PostgreSQL für beabsichtigte Datenbankarbeiten sicher."
    bw_compose up -d postgres
    wait_for_postgres
  else
    log "Keine Datenbankarbeiten vorgesehen; PostgreSQL wird weder gestartet noch neu erstellt."
  fi

  if [[ "$run_migrations" == true ]]; then
    log "Führe beabsichtigte Alembic-Migrationen aus."
    bw_compose run --rm migrate
  else
    log "Alembic-Migrationen werden übersprungen."
  fi

  if [[ "$run_seed" == true ]]; then
    log "Führe beabsichtigtes idempotentes Seed aus."
    bw_compose run --rm seed
  else
    log "Seed wird übersprungen."
  fi

  log "Aktualisiere FastAPI ohne PostgreSQL-Abhängigkeiten neu zu starten."
  bw_compose up -d --no-deps api
  wait_for_api

  log "Aktualisiere das Frontend-Gateway."
  bw_compose up -d --no-deps gateway

  ensure_monitoring_services
  success "API, Frontend und optionale Monitoring-Dienste wurden aktualisiert."
}

deploy_stack() {
  ensure_env_file
  log "Starte PostgreSQL."
  bw_compose up -d postgres
  wait_for_postgres

  log "Führe Alembic-Migrationen aus."
  bw_compose run --rm migrate

  log "Führe idempotentes Seed aus."
  bw_compose run --rm seed

  log "Starte FastAPI."
  bw_compose up -d api
  wait_for_api

  local edge_services=(gateway)
  if is_true "$(read_env ENABLE_MONITORING)"; then
    edge_services+=(uptime-kuma monitoring-gateway)
  fi
  log "Starte Gateway und optionale Betriebsdienste."
  bw_compose_with_profiles up -d --remove-orphans "${edge_services[@]}"
  success "Container-Stack wurde in definierter Reihenfolge gestartet."
}
