#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
usage(){ echo "Usage: backup-recovery.sh --postgres FILE --files FILE [--release FILE]" >&2; exit 2; }
postgres_backup=""; files_backup=""; release_artifact=""
while (($#)); do
  case "$1" in
    --postgres) postgres_backup="${2:-}"; shift 2;;
    --files) files_backup="${2:-}"; shift 2;;
    --release) release_artifact="${2:-}"; shift 2;;
    -h|--help) usage;; *) usage;;
  esac
done
[[ "$EUID" -eq 0 ]] || die "Recovery bundles require root."
for command in age python3 tar sha256sum realpath; do require_command "$command"; done
postgres_backup="$(realpath "$postgres_backup")"; files_backup="$(realpath "$files_backup")"
[[ -f "$postgres_backup" && -f "$files_backup" ]] || die "Database or files backup is missing."
verify_backup_checksum "$postgres_backup"; verify_backup_checksum "$files_backup"
if [[ -z "$release_artifact" ]]; then
  install_root="${RBF_INSTALL_ROOT:-/srv/rbf}"
  release_artifact="$install_root/shared/release-artifacts/current.tar.gz"
fi
release_artifact="$(realpath "$release_artifact")"
[[ -f "$release_artifact" && -f "$release_artifact.sha256" ]] || die "Exact deployed release artifact is unavailable: $release_artifact"
verify_backup_checksum "$release_artifact"
recipient="$(read_env BACKUP_AGE_RECIPIENT)"
[[ "$recipient" =~ ^age1[0-9a-z]{20,}$ ]] || die "BACKUP_AGE_RECIPIENT is missing or invalid."

backup_dir="$INFRA_DIR/data/backups/recovery"; run_dir="$INFRA_DIR/data/control/run"
install -d -m 0700 "$backup_dir" "$run_dir"
stage="$(mktemp -d "$run_dir/recovery-stage.XXXXXX")"; plain="$(mktemp "$run_dir/recovery.XXXXXX.tar.gz")"
cleanup(){ rm -rf "$stage" "$plain"; }; trap cleanup EXIT
install -d -m 0700 "$stage/artifacts/postgres" "$stage/artifacts/files" "$stage/artifacts/release" "$stage/configuration/control-secrets" "$stage/system"
for source in "$postgres_backup" "$postgres_backup.sha256"; do install -m 0600 "$source" "$stage/artifacts/postgres/"; done
[[ ! -f "$postgres_backup.restore.json" ]] || install -m 0600 "$postgres_backup.restore.json" "$postgres_backup.restore.json.sha256" "$stage/artifacts/postgres/"
for source in "$files_backup" "$files_backup.sha256"; do install -m 0600 "$source" "$stage/artifacts/files/"; done
for source in "$release_artifact" "$release_artifact.sha256"; do install -m 0600 "$source" "$stage/artifacts/release/"; done
install -m 0600 "$ENV_FILE" "$stage/configuration/infrastructure.env"
if [[ -d "$INFRA_DIR/data/control/secrets" ]]; then
  while IFS= read -r -d '' secret; do
    relative="${secret#"$INFRA_DIR/data/control/secrets/"}"; target="$stage/configuration/control-secrets/$relative"
    install -d -m 0700 "$(dirname "$target")"; install -m 0600 "$secret" "$target"
  done < <(find "$INFRA_DIR/data/control/secrets" -type f ! -name 'database-restore-approval.json' -print0)
fi
flyway="$(python3 - "$postgres_backup.restore.json" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); print((json.loads(p.read_text()).get('flyway_version') or '') if p.is_file() else '')
PY
)"
cat > "$stage/system/backup-metadata.json" <<JSON
{"version":"$(cat "$REPO_ROOT/VERSION")","flyway_version":"$flyway","release_artifact":"$(basename "$release_artifact")"}
JSON
chmod 600 "$stage/system/backup-metadata.json"
python3 "$SCRIPT_DIR/recovery_bundle.py" create-manifest "$stage" "$(basename "$postgres_backup")" "$(basename "$files_backup")" "$(basename "$release_artifact")"
( cd "$stage" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$plain" . )
output="$backup_dir/rbf-recovery-$(date -u +%Y%m%dT%H%M%SZ).tar.gz.age"; temporary="$output.part.$$"
age -r "$recipient" -o "$temporary" "$plain"; chmod 600 "$temporary"
minimum="${BACKUP_MIN_RECOVERY_BYTES:-4096}"; [[ "$(stat -c %s "$temporary")" -ge "$minimum" ]] || die "Recovery bundle is implausibly small."
mv "$temporary" "$output"; backup_finalize "$output" recovery
[[ -z "${BACKUP_RESULT_FILE:-}" ]] || { printf '%s\n' "$output" > "$BACKUP_RESULT_FILE"; chmod 600 "$BACKUP_RESULT_FILE"; }
retention_days="${BACKUP_RETENTION_DAYS:-$(read_env BACKUP_RETENTION_DAYS)}"
[[ "$retention_days" =~ ^[0-9]+$ ]] || retention_days=14
find "$backup_dir" -type f -mtime "+$retention_days" -delete
success "Encrypted recovery bundle created: $output"
