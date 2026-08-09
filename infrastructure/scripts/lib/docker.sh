#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose_binary() {
  if docker compose version >/dev/null 2>&1; then printf 'docker compose';
  elif command -v docker-compose >/dev/null 2>&1; then printf 'docker-compose';
  else return 1; fi
}

bw_compose() {
  ensure_env_file
  local compose
  compose="$(compose_binary)" || die "Docker Compose was not found."
  local env_files=(--env-file "$ENV_FILE")
  [[ ! -f "$RELEASE_ENV_FILE" ]] || env_files+=(--env-file "$RELEASE_ENV_FILE")
  (cd "$INFRA_DIR" && env -u POSTGRES_USER -u POSTGRES_PASSWORD -u POSTGRES_DB \
    $compose "${env_files[@]}" -f "$COMPOSE_FILE" "$@")
}

compose_profiles() { :; }
bw_compose_with_profiles() {
  local profiles=() value
  value="$(compose_profiles || true)"; [[ -z "$value" ]] || read -r -a profiles <<<"$value"
  bw_compose "${profiles[@]}" "$@"
}

wait_for_postgres() {
  for _ in $(seq 1 60); do
    if bw_compose exec -T postgres pg_isready -U "$(read_env POSTGRES_USER)" -d "$(read_env POSTGRES_DB)" >/dev/null 2>&1 \
      && bw_compose exec -T postgres psql -v ON_ERROR_STOP=1 -Atqc 'select 1' \
        -U "$(read_env POSTGRES_USER)" -d "$(read_env POSTGRES_DB)" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  bw_compose logs --tail=160 postgres >&2 || true
  die "PostgreSQL did not become ready in time."
}

wait_for_api() {
  log "Waiting for Spring Boot readiness."
  for attempt in $(seq 1 90); do
    if bw_compose exec -T api wget -qO- http://127.0.0.1:8080/actuator/health/readiness >/dev/null 2>&1; then
      success "Spring Boot and PostgreSQL are ready."
      return 0
    fi
    (( attempt % 15 )) || log "API is still starting (${attempt}/90)."
    sleep 2
  done
  bw_compose logs --tail=160 api >&2 || true
  die "Spring Boot did not become ready in time."
}

ensure_postgres_service() { bw_compose up -d postgres; wait_for_postgres; }
ensure_monitoring_services() { return 0; }

postgres_sql() {
  bw_compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$(read_env POSTGRES_USER)" -d "$(read_env POSTGRES_DB)" "$@"
}

prepare_flyway_cutover() {
  local state
  state="$(postgres_sql -Atqc "select case when to_regclass(current_schema()||'.flyway_schema_history') is not null then 'flyway' when to_regclass(current_schema()||'.alembic_version') is not null then 'alembic' else 'empty' end")"
  case "$state" in
    flyway) success "Flyway schema history is present." ;;
    empty) log "Empty database; the isolated schema migration boundary will create the schema." ;;
    alembic)
      log "Verifying the one-time Alembic-0025-to-Flyway cutover."
      postgres_sql -f - < "$INFRA_DIR/scripts/migration/verify-alembic-head.sql"
      postgres_sql -f - < "$INFRA_DIR/scripts/migration/adopt-flyway.sql"
      success "Existing database was migrated from Alembic to Flyway in a controlled manner."
      ;;
    *) die "Unknown database schema state: $state" ;;
  esac
}

verify_flyway_schema() {
  local failed
  failed="$(postgres_sql -Atqc "select count(*) from flyway_schema_history where not success" 2>/dev/null || printf 1)"
  [[ "$failed" == 0 ]] || die "Flyway schema history contains failed migrations."
}

run_schema_migrations() {
  log "Running the isolated schema migration boundary."
  bw_compose run --rm --no-deps schema
  verify_flyway_schema
}

quiesce_api_for_database_update() {
  bw_compose ps --status running -q api 2>/dev/null | grep -q . && bw_compose stop api || true
}

deploy_application_update() {
  local _migrate="${1:-true}" _seed="${2:-true}" _restore="${3:-false}" _components="${4:-api,gateway}"
  ensure_postgres_service
  prepare_flyway_cutover
  case ",${_components}," in *,api,*) run_schema_migrations; bw_compose up -d --no-deps api; wait_for_api ;; esac
  case ",${_components}," in *,gateway,*) bw_compose up -d --no-deps gateway ;; esac
}

deploy_stack() {
  ensure_postgres_service
  prepare_flyway_cutover
  run_schema_migrations
  bw_compose up -d --no-deps api
  wait_for_api
  # The API was already started, waited for, and schema-verified above. Do not
  # let Compose reconcile its dependency again: that can recreate/terminate a
  # healthy API container while bringing up the gateway (exit 143).
  bw_compose up -d --no-deps --remove-orphans gateway
  success "Spring Boot stack was started."
}
