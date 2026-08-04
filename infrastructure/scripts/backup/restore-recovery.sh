#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
usage(){ cat >&2 <<'USAGE'
Usage: sudo restore-recovery.sh --identity AGE_KEY --bundle BUNDLE [--verify-only]
       [--yes --replace-existing] [--install-root /opt/rbf] [--report FILE]
USAGE
exit 2; }
identity=""; bundle=""; verify_only=false; confirmed=false; replace_existing=false; report=""; install_root="${RBF_INSTALL_ROOT:-/opt/rbf}"
while (($#)); do
  case "$1" in
    --identity) identity="${2:-}"; shift 2;; --bundle) bundle="${2:-}"; shift 2;;
    --verify-only) verify_only=true; shift;; --yes) confirmed=true; shift;;
    --replace-existing) replace_existing=true; shift;; --install-root) install_root="${2:-}"; shift 2;;
    --report) report="${2:-}"; shift 2;; -h|--help) usage;; *) usage;;
  esac
done
[[ "$EUID" -eq 0 ]] || die "Disaster recovery requires root."
[[ "$verify_only" == true || "$confirmed" == true ]] || die "Use --yes for an actual restore."
[[ -n "$identity" && -n "$bundle" ]] || usage
for command in age python3 tar sha256sum pg_restore; do require_command "$command"; done
identity="$(realpath "$identity")"; bundle="$(realpath "$bundle")"
[[ -f "$identity" && -f "$bundle" ]] || die "Identity or recovery bundle is missing."
verify_backup_checksum "$bundle"
temporary="$(mktemp -d)"; plain="$temporary/recovery.tar.gz"; extracted="$temporary/extracted"
cleanup(){ rm -rf "$temporary"; }; trap cleanup EXIT
age -d -i "$identity" -o "$plain" "$bundle"
manifest="$(python3 "$SCRIPT_DIR/recovery_bundle.py" extract-and-verify "$plain" "$extracted")"
read_artifact(){ python3 -c 'import json,sys; print(json.loads(sys.argv[1])["artifacts"][sys.argv[2]])' "$manifest" "$1"; }
postgres="$extracted/$(read_artifact postgres)"; files="$extracted/$(read_artifact files)"; release="$extracted/$(read_artifact release)"; configuration="$extracted/$(read_artifact configuration)"
for file in "$postgres" "$files" "$release"; do [[ -f "$file" ]] || die "Recovery artifact is missing: $file"; done
verify_backup_checksum "$postgres"; verify_backup_checksum "$files"; verify_backup_checksum "$release"
pg_restore --list "$postgres" >/dev/null || die "PostgreSQL dump inventory is invalid."
release_stage="$temporary/release-check"
release_manifest="$(python3 "$SCRIPT_DIR/../release/verify-artifact.py" "$release" "$release_stage")"
release_version="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["version"])' "$release_manifest")"
report="${report:-$temporary/recovery-verification.json}"
cat > "$report" <<JSON
{"schema_version":2,"status":"passed","checked_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","release_version":"$release_version","database_dump":"$(basename "$postgres")","files_backup":"$(basename "$files")"}
JSON
chmod 600 "$report"
if [[ "$verify_only" == true ]]; then
  [[ "$report" == "$temporary/"* ]] || { sha256sum "$report" > "$report.sha256"; chmod 600 "$report.sha256"; }
  success "Recovery bundle structure, release and PostgreSQL dump verified${report:+: $report}."
  exit 0
fi
[[ -f "$configuration/infrastructure.env" ]] || die "Recovery environment is missing."
if [[ -e "$install_root/current" && "$replace_existing" != true ]]; then
  die "Existing installation detected. Use --replace-existing for a deliberate in-place recovery."
fi
install -d -m 0750 "$install_root/shared" "$install_root/shared/data"
if [[ -f "$install_root/shared/.env" ]]; then
  install -m 0600 "$install_root/shared/.env" "$install_root/shared/.env.before-recovery-$(date -u +%Y%m%dT%H%M%SZ)"
fi
install -m 0600 "$configuration/infrastructure.env" "$install_root/shared/.env"
install -d -m 0700 "$install_root/shared/data/control/secrets"
[[ ! -d "$configuration/control-secrets" ]] || cp -a "$configuration/control-secrets/." "$install_root/shared/data/control/secrets/"
find "$install_root/shared/data/control/secrets" -type d -exec chmod 0700 {} +
find "$install_root/shared/data/control/secrets" -type f -exec chmod 0600 {} +

installed_version="$(cat "$install_root/shared/current-version" 2>/dev/null || true)"
if [[ "$installed_version" != "$release_version" || ! -L "$install_root/current" ]]; then
  install_args=(--artifact "$release" --checksum "$release.sha256" --install-root "$install_root"
    --env "$configuration/infrastructure.env" --requested-by disaster-recovery)
  [[ -L "$install_root/current" ]] || install_args+=(--no-backup)
  "$REPO_ROOT/infrastructure/scripts/release/install-artifact.sh" "${install_args[@]}"
fi
current="$(readlink -f "$install_root/current")"
[[ -x "$current/infrastructure/scripts/backup/restore-data.sh" ]] || die "Installed release lacks restore tooling."
"$current/infrastructure/scripts/backup/restore-data.sh" --yes "$files"
"$current/infrastructure/scripts/backup/restore-postgres.sh" "$postgres"
"$current/infrastructure/scripts/checks/smoke-test.sh"
install -d -m 0700 "$current/infrastructure/data/backups/reports"
final_report="$current/infrastructure/data/backups/reports/rbf-recovery-$(date -u +%Y%m%dT%H%M%SZ).json"
install -m 0600 "$report" "$final_report"; sha256sum "$final_report" > "$final_report.sha256"; chmod 600 "$final_report.sha256"
success "Disaster recovery completed from exact release $release_version. Remove the age identity from the host now."
