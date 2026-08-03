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
  local attempt
  log "Warte auf die API-Readiness."
  for attempt in $(seq 1 90); do
    if bw_compose exec -T api python -c \
      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=4)" \
      >/dev/null 2>&1; then
      success "API und Datenbank sind bereit."
      return 0
    fi
    if (( attempt % 15 == 0 )); then
      log "API startet noch (${attempt}/90 Readiness-Prüfungen)."
    fi
    sleep 2
  done
  warn "API-Readiness blieb aus; Containerstatus und letzte API-Logs folgen."
  bw_compose ps api >&2 || true
  bw_compose logs --tail=120 api >&2 || true
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

ensure_postgres_service() {
  log "Stelle PostgreSQL sicher."
  bw_compose up -d postgres
  wait_for_postgres
}

read_database_schema_state() {
  ensure_env_file
  local database_url="${1:-}" output marker
  local run_args=(run --rm --no-deps -T)
  [[ -z "$database_url" ]] || run_args+=(-e "DATABASE_URL=$database_url")
  run_args+=(migrate python -c)
  output="$(bw_compose "${run_args[@]}" '
from app.db.schema_health import current_alembic_heads, expected_alembic_heads
from app.db.session import engine
with engine.connect() as connection:
    current = ",".join(sorted(current_alembic_heads(connection)))
expected = ",".join(sorted(expected_alembic_heads()))
print(f"RBF_SCHEMA_STATUS|{current}|{expected}|{str(current == expected).lower()}")
')"
  marker="$(printf '%s\n' "$output" | grep '^RBF_SCHEMA_STATUS|' | tail -n 1 || true)"
  [[ -n "$marker" ]] || die "Datenbankrevision konnte nicht aus dem API-Image ermittelt werden."
  IFS='|' read -r _ SCHEMA_CURRENT_HEADS SCHEMA_EXPECTED_HEADS SCHEMA_MATCHES <<<"$marker"
  [[ -n "$SCHEMA_EXPECTED_HEADS" ]] || die "Das API-Image enthält keinen Alembic-Head."
}

verify_database_schema_head() {
  local database_url="${1:-}"
  read_database_schema_state "$database_url"
  if [[ "$SCHEMA_MATCHES" != true ]]; then
    die "Datenbankschema stimmt nicht mit dem API-Image überein (aktuell: ${SCHEMA_CURRENT_HEADS:-keine Revision}; erwartet: $SCHEMA_EXPECTED_HEADS)."
  fi
  success "Datenbankschema entspricht Alembic-Head $SCHEMA_EXPECTED_HEADS."
}

quiesce_api_for_database_update() {
  [[ "${API_QUIESCED_FOR_DATABASE_UPDATE:-false}" != true ]] || return 0
  if bw_compose ps --status running -q api 2>/dev/null | grep -q .; then
    log "Stoppe die API vor Datenbankarbeiten; sie bleibt bis zum geprüften Deployment angehalten."
    bw_compose stop api
    API_QUIESCED_FOR_DATABASE_UPDATE=true
  fi
}

deploy_application_update() {
  local run_migrations="${1:-false}"
  local run_seed="${2:-false}"
  local restore_seed_defaults="${3:-false}"
  local components="${4:-api,secure-api,gateway}"

  ensure_env_file

  if [[ "$run_migrations" == true || "$run_seed" == true ]]; then
    quiesce_api_for_database_update
    log "Stelle PostgreSQL für beabsichtigte Datenbankarbeiten sicher."
    ensure_postgres_service
  elif [[ ",${components}," == *,api,* ]]; then
    log "Keine Datenbankarbeiten vorgesehen; PostgreSQL wurde bereits für die Revisionsprüfung validiert."
  else
    log "Keine API-Komponente ausgewählt; Datenbankdienste bleiben unangetastet."
  fi

  if [[ "$run_migrations" == true ]]; then
    log "Führe beabsichtigte Alembic-Migrationen aus."
    # From this point on, reverting only the application image could make code
    # and schema incompatible even if the migration command later fails.
    DATABASE_ACTIONS_EXECUTED=true
    bw_compose run --rm migrate
  else
    log "Alembic-Migrationen werden übersprungen."
  fi

  if [[ "$run_seed" == true ]]; then
    DATABASE_ACTIONS_EXECUTED=true
    if [[ "$restore_seed_defaults" == true ]]; then
      log "Stelle repository-eigene Seed-Defaults wieder her und führe das Seed aus."
      bw_compose run --rm seed rbf-seed --restore-seed-defaults
    else
      log "Führe beabsichtigtes idempotentes Seed aus."
      bw_compose run --rm seed
    fi
  else
    log "Seed wird übersprungen."
  fi

  if [[ ",${components}," == *,api,* ]]; then
    verify_database_schema_head
    log "Aktualisiere FastAPI ohne PostgreSQL-Abhängigkeiten neu zu starten."
    bw_compose up -d --no-deps api
    wait_for_api
  fi
  if [[ ",${components}," == *,secure-api,* ]]; then
    log "Aktualisiere die Spring-Security-API."
    bw_compose up -d --no-deps secure-api
  fi
  if [[ ",${components}," == *,gateway,* ]]; then
    log "Aktualisiere das Frontend-Gateway."
    bw_compose up -d --no-deps gateway
  fi

  ensure_monitoring_services
  success "Ausgewählte Komponenten (${components}) und optionale Monitoring-Dienste wurden aktualisiert."
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
