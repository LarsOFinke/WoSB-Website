#!/usr/bin/env bash
set -Eeuo pipefail

database_action_summary() {
  local actions=()
  [[ "$RUN_MIGRATIONS" == true ]] && actions+=("Migrationen")
  [[ "$RUN_SEED" == true ]] && actions+=("Seed")

  if ((${#actions[@]} == 0)); then
    printf 'keine Schemaänderung; PostgreSQL wurde nur auf Revisionsgleichheit geprüft'
  else
    local joined
    joined="$(IFS=', '; echo "${actions[*]}")"
    printf '%s' "$joined"
  fi
}

update_prepare_control_files() {
  mkdir -p "$INBOX_DIR" "$STATUS_DIR" "$RUN_DIR"
  chown 10001:10001 "$INBOX_DIR"
  chown root:root "$STATUS_DIR" "$RUN_DIR"
  chmod 700 "$INBOX_DIR" "$RUN_DIR"
  chmod 755 "$STATUS_DIR"
  touch "$LOG_FILE"
  chown root:root "$LOG_FILE"
  chmod 644 "$LOG_FILE"
}

update_acquire_lock() {
  exec 9>"$LOCK_FILE"
  if flock -n 9; then
    LOCK_ACQUIRED=true
    return 0
  fi

  if [[ -e "$INBOX_REQUEST_FILE" ]]; then
    local wait_seconds="${UPDATE_LOCK_WAIT_SECONDS:-600}"
    warn "Ein anderes Server-Update läuft bereits; die Admin-Anforderung bleibt in der Inbox und wartet bis zu ${wait_seconds}s auf den exklusiven Lock."
    if flock -w "$wait_seconds" 9; then
      LOCK_ACQUIRED=true
      return 0
    fi
    warn "Der Update-Lock wurde nicht rechtzeitig frei; die Admin-Anforderung bleibt unverändert in der Inbox."
    return 1
  fi
  die "Ein anderes Server-Update läuft bereits."
}

update_claim_admin_request() {
  [[ -e "$INBOX_REQUEST_FILE" ]] || return 0
  rm -f "$REQUEST_FILE"
  claim_control_request "$INBOX_REQUEST_FILE" "$REQUEST_FILE" 10001
}

update_capture_service_image() {
  local service="$1" id_var="$2" tag_var="$3" container image_id image_tag
  container="$(bw_compose ps -q "$service" 2>/dev/null || true)"
  [[ -n "$container" ]] || return 0
  image_id="$(docker inspect --format '{{.Image}}' "$container" 2>/dev/null || true)"
  image_tag="$(docker inspect --format '{{.Config.Image}}' "$container" 2>/dev/null || true)"
  [[ -n "$image_id" && -n "$image_tag" ]] || return 0
  printf -v "$id_var" '%s' "$image_id"
  printf -v "$tag_var" '%s' "$image_tag"
}

update_capture_running_images() {
  update_capture_service_image api API_IMAGE_BEFORE API_IMAGE_TAG_BEFORE
  update_capture_service_image gateway GATEWAY_IMAGE_BEFORE GATEWAY_IMAGE_TAG_BEFORE
  if [[ -n "$API_IMAGE_BEFORE" && -n "$GATEWAY_IMAGE_BEFORE" ]]; then
    log "Laufende API- und Gateway-Images wurden als exakter Rollback-Punkt erfasst."
  else
    warn "Nicht alle laufenden Images konnten erfasst werden; ein Rollback kann einen Rebuild benötigen."
  fi
}

update_restore_captured_images() {
  [[ -n "$API_IMAGE_BEFORE" && -n "$API_IMAGE_TAG_BEFORE" ]] || return 1
  [[ -n "$GATEWAY_IMAGE_BEFORE" && -n "$GATEWAY_IMAGE_TAG_BEFORE" ]] || return 1
  docker image inspect "$API_IMAGE_BEFORE" >/dev/null 2>&1 || return 1
  docker image inspect "$GATEWAY_IMAGE_BEFORE" >/dev/null 2>&1 || return 1

  docker image tag "$API_IMAGE_BEFORE" "$API_IMAGE_TAG_BEFORE"
  docker image tag "$GATEWAY_IMAGE_BEFORE" "$GATEWAY_IMAGE_TAG_BEFORE"
  bw_compose up -d --no-deps api
  wait_for_api
  bw_compose up -d --no-deps gateway
  ensure_monitoring_services
  /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
}

update_create_backup() {
  [[ "$CREATE_BACKUP" == true ]] || return 0

  if [[ "$RUN_MIGRATIONS" == true || "$RUN_SEED" == true ]]; then
    log "Erstelle Sicherheitsbackup inklusive PostgreSQL vor beabsichtigten Datenbankarbeiten."
    /usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-all.sh"
  else
    log "Erstelle Datei-Backup; das geprüfte PostgreSQL-Schema bleibt unverändert."
    /usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-data.sh"
  fi
}

update_resolve_database_actions() {
  ensure_postgres_service
  read_database_schema_state
  if [[ "$SCHEMA_MATCHES" == true ]]; then
    log "Datenbank ist bereits auf Alembic-Head $SCHEMA_EXPECTED_HEADS."
    return 0
  fi

  if [[ "$RUN_MIGRATIONS" == true ]]; then
    log "Ausstehende Migration erkannt (${SCHEMA_CURRENT_HEADS:-keine Revision} → $SCHEMA_EXPECTED_HEADS); expliziter Migrationsmodus ist aktiv."
    return 0
  fi

  if [[ "$AUTO_MIGRATIONS" == true ]]; then
    RUN_MIGRATIONS=true
    update_refresh_operation
    log "Ausstehende Migration erkannt (${SCHEMA_CURRENT_HEADS:-keine Revision} → $SCHEMA_EXPECTED_HEADS); Migration wird automatisch ausgeführt."
    return 0
  fi

  die "Datenbank ist nicht auf dem Alembic-Head des neuen API-Images (${SCHEMA_CURRENT_HEADS:-keine Revision} → $SCHEMA_EXPECTED_HEADS). Deployment wegen --no-auto-migrate abgebrochen."
}

update_execute_deployment() {
  ensure_monitoring_services
  update_status_write \
    running \
    "API und Frontend werden gebaut; anschließend wird der Datenbankstand mit dem Image verglichen." \
    "$STARTED_AT" "" "$COMMIT_BEFORE" "$COMMIT_AFTER"

  bw_compose build --pull api gateway
  update_resolve_database_actions

  update_status_write \
    running \
    "Deployment wird ausgeführt. Datenbankaktionen: $(database_action_summary)." \
    "$STARTED_AT" "" "$COMMIT_BEFORE" "$COMMIT_AFTER"

  # Create the recovery point only after the final database action is known and
  # before executing any newly pulled host installer or schema mutation.
  update_create_backup
  log "Aktualisiere systemd-Units und Host-Runner."
  /usr/bin/env bash "$INFRA_DIR/scripts/deployment/install-systemd.sh"

  deploy_application_update "$RUN_MIGRATIONS" "$RUN_SEED"
  /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
}

update_attempt_rollback() {
  if [[ "$RUN_MIGRATIONS" == true || "$RUN_SEED" == true ]]; then
    warn "Automatischer Code-Rollback wird nach Datenbankaktionen konservativ übersprungen."
    return 1
  fi

  warn "Versuche automatischen Rollback auf die zuvor laufenden Images."
  set +e
  local reset_code=0 rollback_code=1
  if [[ -d "$REPO_ROOT/.git" && -n "$COMMIT_BEFORE" && -n "$COMMIT_AFTER" && "$COMMIT_BEFORE" != "$COMMIT_AFTER" ]]; then
    git_as_owner reset --hard "$COMMIT_BEFORE"
    reset_code=$?
  fi

  if [[ "$reset_code" -eq 0 ]]; then
    if /usr/bin/env bash "$INFRA_DIR/scripts/deployment/install-systemd.sh"; then
      if ( update_restore_captured_images ); then
        rollback_code=0
      else
        warn "Exakte frühere Images sind nicht verfügbar; versuche Rebuild des vorherigen Commits."
        (
          bw_compose build api gateway \
            && deploy_application_update false false \
            && /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
        )
        rollback_code=$?
      fi
    else
      rollback_code=$?
    fi
  else
    rollback_code=$reset_code
  fi
  set -e

  if [[ "$rollback_code" -eq 0 ]]; then
    warn "Automatischer Rollback war erfolgreich."
    return 0
  fi
  warn "Automatischer Rollback ist ebenfalls fehlgeschlagen (Exit $rollback_code)."
  return 1
}

update_on_exit() {
  local exit_code=$?
  update_heartbeat_stop
  if [[ "$UPDATE_COMPLETED" != true && "$exit_code" -ne 0 ]]; then
    local finished message
    finished="$(now_iso)"
    message="Server-Update fehlgeschlagen (Exit ${exit_code})."
    if update_attempt_rollback; then
      message="$message Der vorherige Code- und Image-Stand wurde automatisch wiederhergestellt."
    else
      message="$message Automatischer Rollback war nicht möglich oder wurde aus Sicherheitsgründen übersprungen."
    fi
    update_status_write \
      failed \
      "$message" \
      "$STARTED_AT" "$finished" "$COMMIT_BEFORE" "$COMMIT_AFTER" || true
    warn "Server-Update fehlgeschlagen. Details: $LOG_FILE"
  fi
}

update_run() {
  update_prepare_control_files
  if ! update_acquire_lock; then
    return 0
  fi

  # The request is claimed only after the exclusive lock is held. This prevents
  # concurrent services from consuming or overwriting each other's work.
  update_claim_admin_request
  update_apply_request_file

  if [[ -n "$INVALID_REQUEST_OPERATION" ]]; then
    update_status_write failed "Ungültiger Update-Modus in der Admin-Anforderung." "" "$(now_iso)"
    die "Ungültiger Update-Modus in der Admin-Anforderung: $INVALID_REQUEST_OPERATION"
  fi

  STARTED_AT="$(now_iso)"
  update_status_write running "Server-Update wird vorbereitet." "$STARTED_AT"
  update_heartbeat_start
  exec > >(tee -a "$LOG_FILE") 2>&1
  trap update_on_exit EXIT

  log "Server-Update angefordert von: $REQUESTED_BY"
  update_capture_running_images
  update_repository
  update_execute_deployment

  FINISHED_AT="$(now_iso)"
  update_heartbeat_stop
  update_status_write \
    succeeded \
    "Server-Update erfolgreich abgeschlossen. Datenbankaktionen: $(database_action_summary)." \
    "$STARTED_AT" "$FINISHED_AT" "$COMMIT_BEFORE" "$COMMIT_AFTER"
  UPDATE_COMPLETED=true
  success "Server-Update erfolgreich abgeschlossen (${COMMIT_BEFORE:-unbekannt} → ${COMMIT_AFTER:-unbekannt})."
}
