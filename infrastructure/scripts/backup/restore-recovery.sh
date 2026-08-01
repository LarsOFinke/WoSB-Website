#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
source "$INFRA_DIR/scripts/lib/docker.sh"

usage() {
  cat <<'USAGE'
Usage:
  sudo restore-recovery.sh --yes --identity /path/age-key.txt \
    --bundle /path/rbf-recovery-*.tar.gz.age [--restore-versioned-config] [--replace-existing]
  sudo restore-recovery.sh --verify-only --identity /path/age-key.txt \
    --bundle /path/rbf-recovery-*.tar.gz.age [--report FILE]

Restores a complete RBF installation into the current repository checkout.
The script installs host dependencies through setup, restores runtime secrets,
files and PostgreSQL, migrates to the checkout's Alembic head and runs smoke tests.
USAGE
}

confirmed=false
verify_only=false
allow_legacy=false
allow_uncoordinated=false
restore_versioned_config=false
replace_existing=false
report_path=""
identity=""
bundle=""
while (($#)); do
  case "$1" in
    --yes) confirmed=true; shift ;;
    --verify-only) verify_only=true; shift ;;
    --allow-legacy-metadata) allow_legacy=true; shift ;;
    --allow-uncoordinated) allow_uncoordinated=true; shift ;;
    --report) report_path="${2:-}"; shift 2 ;;
    --identity) identity="${2:-}"; shift 2 ;;
    --bundle) bundle="${2:-}"; shift 2 ;;
    --restore-versioned-config) restore_versioned_config=true; shift ;;
    --replace-existing) replace_existing=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unbekannte Option: $1" ;;
  esac
done

[[ "$EUID" -eq 0 ]] || die "Disaster-Recovery benötigt root-Rechte."
if [[ "$verify_only" != true ]]; then
  [[ "$confirmed" == true ]] || die "Diese Aktion überschreibt Laufzeitdaten. Wiederhole mit --yes."
fi
existing_runtime=false
if [[ -f "$INFRA_DIR/data/postgres/PG_VERSION" ]]   || find "$INFRA_DIR/data/uploads" -mindepth 1 -print -quit 2>/dev/null | grep -q .; then
  existing_runtime=true
fi
if [[ "$verify_only" != true && "$existing_runtime" == true && "$replace_existing" != true ]]; then
  die "Bestehende Laufzeitdaten erkannt. Für eine bewusste In-Place-Wiederherstellung zusätzlich --replace-existing verwenden."
fi
require_command age
require_command python3
require_command tar
require_command sha256sum
identity="$(realpath "$identity")"
bundle="$(realpath "$bundle")"
[[ -f "$identity" ]] || die "age-Identität fehlt: $identity"
[[ -f "$bundle" ]] || die "Recovery-Bundle fehlt: $bundle"
[[ -f "${bundle}.sha256" ]] || die "Recovery-Prüfsumme fehlt: ${bundle}.sha256"
verify_backup_checksum "$bundle"

temporary_dir="$(mktemp -d)"
plain_bundle="$temporary_dir/recovery.tar.gz"
extracted="$temporary_dir/extracted"
cleanup() { rm -rf "$temporary_dir"; }
trap cleanup EXIT
chmod 700 "$temporary_dir"

log "Entschlüssele und verifiziere das Recovery-Bundle vollständig."
age -d -i "$identity" -o "$plain_bundle" "$bundle"
manifest_json="$(python3 "$SCRIPT_DIR/recovery_bundle.py" extract-and-verify "$plain_bundle" "$extracted")"

postgres_relative="$(python3 - "$manifest_json" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["artifacts"]["postgres"])
PY
)"
files_relative="$(python3 - "$manifest_json" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["artifacts"]["files"])
PY
)"
backup_version="$(python3 - "$manifest_json" <<'PY'
import json, sys
print((json.loads(sys.argv[1]).get("application") or {}).get("version") or "")
PY
)"
current_version="$(cat "$REPO_ROOT/VERSION" 2>/dev/null || true)"
if [[ -n "$backup_version" && -n "$current_version" && "$backup_version" != "$current_version" ]]; then
  warn "Bundle-Version $backup_version wird mit Checkout-Version $current_version wiederhergestellt; Migrationen werden anschließend ausgeführt."
fi

configuration="$extracted/configuration"
files_backup="$extracted/$files_relative"
postgres_backup="$extracted/$postgres_relative"
[[ -f "$files_backup" && -f "$postgres_backup" ]] || die "Recovery-Artefakte fehlen trotz gültigem Manifest."

if [[ "$verify_only" == true ]]; then
  [[ -f "$configuration/infrastructure.env" ]] || die "Recovery-Bundle enthält keine infrastructure.env."
  recovered_keys="$(python3 - "$configuration/infrastructure.env" <<'PYKEYS'
from pathlib import Path
import sys
for raw in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    if raw.startswith("WEBHOOK_ENCRYPTION_KEYS="):
        value = raw.split("=", 1)[1].strip().strip('"').strip("'")
        print(value)
        break
PYKEYS
  )"
  [[ -n "$recovered_keys" ]] || die "Recovery-Bundle enthält keinen WEBHOOK_ENCRYPTION_KEYS-Schlüsselring."
  if [[ -z "$report_path" ]]; then
    install -d -m 0700 "$INFRA_DIR/data/backups/reports"
    report_path="$INFRA_DIR/data/backups/reports/rbf-recovery-preflight-$(date -u +%Y%m%dT%H%M%SZ)-$$.json"
  fi
  restore_args=(--preflight-only --report "$report_path")
  [[ "$allow_legacy" == true ]] && restore_args+=(--allow-legacy-metadata)
  [[ "$allow_uncoordinated" == true ]] && restore_args+=(--allow-uncoordinated)
  RBF_RESTORE_WEBHOOK_KEYS="$recovered_keys" \
    /usr/bin/env bash "$SCRIPT_DIR/restore-postgres.sh" "${restore_args[@]}" "$postgres_backup"
  success "Recovery-Bundle ist mit dem aktuellen Checkout vollständig wiederherstellbar. Bericht: $report_path"
  exit 0
fi

verify_recovery_keyring() {
  local keyring_file="$configuration/secret-keyring.json" current_fingerprints
  if [[ ! -f "$keyring_file" ]]; then
    warn "Älteres Recovery-Bundle ohne Schlüsselring-Metadaten; die Datenbank-Preflight-Prüfung übernimmt die Kompatibilitätskontrolle."
    return 0
  fi
  current_fingerprints="$(python3 "$SCRIPT_DIR/backup_metadata.py" fingerprints "$ENV_FILE")"
  python3 - "$keyring_file" "$current_fingerprints" <<'PY'
import json, sys
from pathlib import Path
expected_payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = set(expected_payload.get("secret_key_fingerprints") or [])
current = set(json.loads(sys.argv[2]))
if not expected or not expected.issubset(current):
    raise SystemExit(
        "The restored environment does not contain the encryption key ring recorded in the recovery bundle."
    )
PY
}
[[ -f "$configuration/infrastructure.env" ]] || die "Recovery-Bundle enthält keine infrastructure.env."
if [[ -f "$ENV_FILE" ]]; then
  safety_env="$INFRA_DIR/.env.before-recovery-$(date -u +%Y%m%dT%H%M%SZ)"
  install -m 0600 "$ENV_FILE" "$safety_env"
  warn "Vorhandene .env wurde gesichert: $safety_env"
fi
install -m 0600 "$configuration/infrastructure.env" "$ENV_FILE"
verify_recovery_keyring

if [[ -f "$configuration/first-run-credentials.txt" ]]; then
  install -m 0600 "$configuration/first-run-credentials.txt" "$INFRA_DIR/first-run-credentials.txt"
fi
if [[ -f "$configuration/frontend.env" ]]; then
  install -m 0600 "$configuration/frontend.env" "$REPO_ROOT/frontend/.env"
fi

install -d -m 0700 "$INFRA_DIR/data/control/secrets"
if [[ -d "$configuration/control-secrets" ]]; then
  cp -a "$configuration/control-secrets/." "$INFRA_DIR/data/control/secrets/"
  chown -R root:root "$INFRA_DIR/data/control/secrets"
  find "$INFRA_DIR/data/control/secrets" -type d -exec chmod 0700 {} +
  find "$INFRA_DIR/data/control/secrets" -type f -exec chmod 0600 {} +
fi

if [[ "$restore_versioned_config" == true ]]; then
  warn "Versionsverwaltete backend/config/*.cfg werden bewusst aus dem Backup überschrieben."
  install -d -m 0755 "$REPO_ROOT/backend/config"
  for cfg in "$configuration/backend-config"/*.cfg; do
    [[ -f "$cfg" ]] || continue
    install -m 0644 "$cfg" "$REPO_ROOT/backend/config/$(basename "$cfg")"
  done
else
  install -d -m 0700 "$INFRA_DIR/data/recovered-config"
  rm -rf "$INFRA_DIR/data/recovered-config/backend-config"
  cp -a "$configuration/backend-config" "$INFRA_DIR/data/recovered-config/backend-config"
  chown -R root:root "$INFRA_DIR/data/recovered-config"
  warn "Gesicherte .cfg-Dateien wurden zur Prüfung unter infrastructure/data/recovered-config abgelegt, nicht über den aktuellen Code geschrieben."
fi

profile="core"
if is_true "$(read_env ENABLE_MONITORING)"; then
  profile="full"
fi

log "Provisioniere den frischen Host reproduzierbar, starte Container aber noch nicht."
/usr/bin/env bash "$REPO_ROOT/setup.sh" --profile "$profile" --no-start
verify_recovery_keyring

log "Stelle Uploads, Zertifikate, Let's-Encrypt- und Monitoring-Daten wieder her."
/usr/bin/env bash "$SCRIPT_DIR/restore-data.sh" --yes "$files_backup"

log "Hole und baue die für den Restore benötigten Container-Images."
bw_compose_with_profiles pull postgres
if [[ "$profile" == full ]]; then
  bw_compose_with_profiles pull uptime-kuma
fi
bw_compose build api gateway

log "Stelle PostgreSQL wieder her, migriere und prüfe die Anwendung."
/usr/bin/env bash "$SCRIPT_DIR/restore-postgres.sh" "$postgres_backup"

log "Synchronisiere idempotente System- und Stammdaten des aktuellen Checkouts."
bw_compose run --rm seed
bw_compose restart api
wait_for_api
bw_compose restart gateway
ensure_monitoring_services
/usr/bin/env bash "$INFRA_DIR/scripts/checks/smoke-test.sh"

success "Disaster-Recovery vollständig abgeschlossen. Entferne die age-Identitätsdatei jetzt wieder vom Server."
