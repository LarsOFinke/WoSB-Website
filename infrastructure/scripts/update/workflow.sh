#!/usr/bin/env bash
set -Eeuo pipefail

database_action_summary() {
  local actions=()
  [[ "$RUN_MIGRATIONS" == true ]] && actions+=("Migrationen")
  [[ "$RUN_SEED" == true ]] && actions+=("Seed")

  if ((${#actions[@]} == 0)); then
    printf 'keine; PostgreSQL bleibt unverändert'
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

update_claim_admin_request() {
  [[ -e "$INBOX_REQUEST_FILE" ]] || return 0
  rm -f "$REQUEST_FILE"
  claim_control_request "$INBOX_REQUEST_FILE" "$REQUEST_FILE" 10001
}

update_create_backup() {
  [[ "$CREATE_BACKUP" == true ]] || return 0

  if [[ "$RUN_MIGRATIONS" == true || "$RUN_SEED" == true ]]; then
    log "Erstelle Sicherheitsbackup inklusive PostgreSQL vor beabsichtigten Datenbankarbeiten."
    /usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-all.sh"
  else
    log "Erstelle Datei-Backup; PostgreSQL wird für dieses Code-Update nicht angesprochen."
    /usr/bin/env bash "$INFRA_DIR/scripts/backup/backup-data.sh"
  fi
}

update_execute_deployment() {
  log "Datenbankaktionen: $(database_action_summary)."
  # Create the recovery point before executing any newly pulled host installer.
  update_create_backup
  log "Aktualisiere systemd-Units und Host-Runner."
  /usr/bin/env bash "$INFRA_DIR/scripts/deployment/install-systemd.sh"

  ensure_monitoring_services
  update_status_write \
    running \
    "API und Frontend werden gebaut. Datenbankaktionen: $(database_action_summary)." \
    "$STARTED_AT" "" "$COMMIT_BEFORE" "$COMMIT_AFTER"

  bw_compose build --pull api gateway
  ensure_monitoring_services
  deploy_application_update "$RUN_MIGRATIONS" "$RUN_SEED"
  /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
}

update_attempt_rollback() {
  [[ -d "$REPO_ROOT/.git" ]] || return 1
  [[ -n "$COMMIT_BEFORE" && -n "$COMMIT_AFTER" && "$COMMIT_BEFORE" != "$COMMIT_AFTER" ]] || return 1
  if [[ "$RUN_MIGRATIONS" == true || "$RUN_SEED" == true ]]; then
    warn "Automatischer Code-Rollback wird nach Datenbankaktionen konservativ übersprungen."
    return 1
  fi

  warn "Versuche automatischen Rollback auf Commit $COMMIT_BEFORE."
  set +e
  git_as_owner reset --hard "$COMMIT_BEFORE"
  local reset_code=$?
  if [[ "$reset_code" -eq 0 ]]; then
    /usr/bin/env bash "$INFRA_DIR/scripts/deployment/install-systemd.sh" \
      && bw_compose build api gateway \
      && deploy_application_update false false \
      && /usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"
    local rollback_code=$?
  else
    local rollback_code=$reset_code
  fi
  set -e

  if [[ "$rollback_code" -eq 0 ]]; then
    warn "Automatischer Rollback auf $COMMIT_BEFORE war erfolgreich."
    return 0
  fi
  warn "Automatischer Rollback ist ebenfalls fehlgeschlagen (Exit $rollback_code)."
  return 1
}

update_on_exit() {
  local exit_code=$?
  if [[ "$UPDATE_COMPLETED" != true && "$exit_code" -ne 0 ]]; then
    local finished message
    finished="$(now_iso)"
    message="Server-Update fehlgeschlagen (Exit ${exit_code})."
    if update_attempt_rollback; then
      message="$message Der vorherige Code-Stand wurde automatisch wiederhergestellt."
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
  update_claim_admin_request
  update_apply_request_file

  if [[ -n "$INVALID_REQUEST_OPERATION" ]]; then
    update_status_write failed "Ungültiger Update-Modus in der Admin-Anforderung." "" "$(now_iso)"
    die "Ungültiger Update-Modus in der Admin-Anforderung: $INVALID_REQUEST_OPERATION"
  fi

  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    update_status_write failed "Ein anderes Server-Update läuft bereits." "" "$(now_iso)"
    die "Ein anderes Server-Update läuft bereits."
  fi

  STARTED_AT="$(now_iso)"
  update_status_write running "Server-Update wird vorbereitet." "$STARTED_AT"
  exec > >(tee -a "$LOG_FILE") 2>&1
  trap update_on_exit EXIT

  log "Server-Update angefordert von: $REQUESTED_BY"
  update_repository
  update_execute_deployment

  FINISHED_AT="$(now_iso)"
  update_status_write \
    succeeded \
    "Server-Update erfolgreich abgeschlossen. Datenbankaktionen: $(database_action_summary)." \
    "$STARTED_AT" "$FINISHED_AT" "$COMMIT_BEFORE" "$COMMIT_AFTER"
  UPDATE_COMPLETED=true
  success "Server-Update erfolgreich abgeschlossen (${COMMIT_BEFORE:-unbekannt} → ${COMMIT_AFTER:-unbekannt})."
}
