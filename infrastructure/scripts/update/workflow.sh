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
  mkdir -p "$CONTROL_DIR"
  chmod 770 "$CONTROL_DIR"
  touch "$LOG_FILE"
  chmod 664 "$LOG_FILE"
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
  log "Aktualisiere systemd-Units und Host-Runner."
  /usr/bin/env bash "$INFRA_DIR/scripts/deployment/install-systemd.sh"
  update_create_backup

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

update_on_exit() {
  local exit_code=$?
  if [[ "$UPDATE_COMPLETED" != true && "$exit_code" -ne 0 ]]; then
    local finished
    finished="$(now_iso)"
    update_status_write \
      failed \
      "Server-Update fehlgeschlagen (Exit ${exit_code})." \
      "$STARTED_AT" "$finished" "$COMMIT_BEFORE" "$COMMIT_AFTER" || true
    warn "Server-Update fehlgeschlagen. Details: $LOG_FILE"
  fi
}

update_run() {
  update_prepare_control_files
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
