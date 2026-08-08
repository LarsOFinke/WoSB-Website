#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
source "$INFRA_DIR/scripts/lib/env.sh"
source "$INFRA_DIR/scripts/backup/common.sh"

"$INFRA_DIR/scripts/checks/preflight.sh" runtime
if [[ "$EUID" -eq 0 ]]; then
  "$INFRA_DIR/scripts/checks/host-security.sh"
else
  warn "Host security check skipped; use sudo for the complete check."
fi
validate_env
bw_compose_with_profiles config >/dev/null
success "Compose and environment configuration are valid."

log "Containerstatus"
bw_compose_with_profiles ps

log "Speicherbelegung"
df -h "$INFRA_DIR"

backup_count="$(find "$INFRA_DIR/data/backups" -mindepth 2 -type f ! -name '*.sha256' 2>/dev/null | wc -l | tr -d ' ')"
log "Local backup files: ${backup_count:-0}"

backup_health="$INFRA_DIR/data/control/status/backup-health.json"
if [[ -f "$backup_health" ]]; then
  backup_set="$(python3 - "$backup_health" "${BACKUP_MAX_AGE_HOURS:-$(read_env BACKUP_MAX_AGE_HOURS)}" <<'PYHEALTH'
from datetime import datetime, timezone
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
max_age = float(sys.argv[2] or 36)
payload = json.loads(path.read_text(encoding="utf-8"))
if payload.get("schema_version") != 2 or payload.get("status") != "succeeded":
    raise SystemExit("Latest coordinated backup did not finish successfully.")
finished = datetime.fromisoformat(str(payload.get("finished_at") or "").replace("Z", "+00:00"))
if finished.tzinfo is None:
    finished = finished.replace(tzinfo=timezone.utc)
age = (datetime.now(timezone.utc) - finished.astimezone(timezone.utc)).total_seconds() / 3600
if age > max_age:
    raise SystemExit(f"Latest committed backup set is stale ({age:.1f}h > {max_age:.1f}h).")
artifacts = payload.get("artifacts")
backup_set = artifacts.get("backup_set") if isinstance(artifacts, dict) else ""
if not backup_set:
    raise SystemExit("Backup health record has no committed backup set.")
print(backup_set)
PYHEALTH
  )" || die "Backup health status is invalid or stale."
  [[ -f "$backup_set" ]] || die "Set referenced by backup health status is missing: $backup_set"
  manifest_root="$(backup_manifest_root)"
  python3 "$INFRA_DIR/scripts/backup/backup_set_manifest.py" validate --root "$manifest_root" "$backup_set" >/dev/null \
    || die "Latest backup set is incomplete or not recovery-verified."
  success "Latest coordinated backup set is current, complete, and recovery-verified."
else
  warn "No machine-readable backup health status exists yet. Run sudo make -C infrastructure backup."
fi

if is_true "$(read_env BACKUP_RECOVERY_ENABLED)"; then
  recipient="$(read_env BACKUP_AGE_RECIPIENT)"
  [[ "$recipient" =~ ^age1[0-9a-z]{20,}$ ]]     || die "Recovery backup is enabled, but BACKUP_AGE_RECIPIENT is invalid."
  latest_recovery="$(find "$INFRA_DIR/data/backups/recovery" -maxdepth 1 -type f -name 'rbf-recovery-*.tar.gz.age' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
  if [[ -n "$latest_recovery" ]]; then
    verify_backup_checksum "$latest_recovery"
    log "Latest encrypted recovery bundle: $latest_recovery"
  else
    warn "Recovery backup is enabled, but no bundle exists yet."
  fi
  export_dir="$(read_env BACKUP_PULL_EXPORT_DIR)"
  export_user="$(read_env BACKUP_PULL_EXPORT_USER)"
  if [[ -n "$export_dir" || -n "$export_user" ]]; then
    [[ -n "$export_dir" && -n "$export_user" ]]       || die "BACKUP_PULL_EXPORT_DIR and BACKUP_PULL_EXPORT_USER must be set together."
    [[ -d "$export_dir" ]] || warn "Pull export directory does not exist yet: $export_dir"
    id "$export_user" >/dev/null 2>&1 || die "Pull export user does not exist: $export_user"
  fi
else
  warn "Complete encrypted disaster recovery is disabled."
fi

if bw_compose ps --status running api gateway postgres 2>/dev/null | grep -q .; then
  "$INFRA_DIR/scripts/checks/smoke-test.sh"
else
  warn "At least one core service is not running; smoke test was skipped."
fi
