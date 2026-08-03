#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  sudo install-artifact.sh --artifact FILE [options]

Options:
  --artifact FILE          Deployment-Artifact (required)
  --checksum FILE         äußere SHA-256-Datei (default: FILE.sha256)
  --update-script FILE    Update-Einstiegspunkt (default: ./update.sh)
  --components LIST       api,secure-api,gateway
  --migrate               Alembic-Migrationen ausführen
  --seed                  Migrationen und idempotentes Seed ausführen
  --no-auto-migrate       Bei veralteter Datenbank abbrechen
  --no-backup              Vorab-Backup überspringen
  --requested-by NAME     Bediener für den Update-Status
  -h, --help              Show this help
USAGE
  exit 2
}

die() { echo "[error] $*" >&2; exit 1; }

artifact=""
checksum=""
update_script="./update.sh"
components=""
requested_by=""
migrate=false
seed=false
no_auto_migrate=false
no_backup=false

while (($#)); do
  case "$1" in
    --artifact) artifact="${2:-}"; shift 2 ;;
    --checksum) checksum="${2:-}"; shift 2 ;;
    --update-script) update_script="${2:-}"; shift 2 ;;
    --components) components="${2:-}"; shift 2 ;;
    --migrate) migrate=true; shift ;;
    --seed) seed=true; shift ;;
    --no-auto-migrate) no_auto_migrate=true; shift ;;
    --no-backup) no_backup=true; shift ;;
    --requested-by) requested_by="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

[[ "$EUID" -eq 0 ]] || die "Als root ausführen, z. B. sudo $0 ..."
[[ -n "$artifact" ]] || die "--artifact FILE ist erforderlich."
[[ -f "$artifact" ]] || die "Deployment-Artifact nicht gefunden: $artifact"
[[ -n "$checksum" ]] || checksum="$artifact.sha256"
[[ -f "$checksum" ]] || die "Prüfsumme nicht gefunden: $checksum"
[[ -x "$update_script" ]] || die "Update-Skript fehlt oder ist nicht ausführbar: $update_script"

(cd "$(dirname "$artifact")" && sha256sum --check "$checksum")

update_args=(--artifact "$artifact")
[[ -z "$components" ]] || update_args+=(--components "$components")
[[ "$migrate" == true ]] && update_args+=(--migrate)
[[ "$seed" == true ]] && update_args+=(--seed)
[[ "$no_auto_migrate" == true ]] && update_args+=(--no-auto-migrate)
[[ "$no_backup" == true ]] && update_args+=(--no-backup)
[[ -z "$requested_by" ]] || update_args+=(--requested-by "$requested_by")

exec "$update_script" "${update_args[@]}"
