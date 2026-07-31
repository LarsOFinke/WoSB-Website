#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

usage() {
  cat <<'USAGE'
Usage:
  backup-recovery.sh --postgres /path/backup.sql.gz --files /path/rbf-files.tar.gz

Creates one age-encrypted disaster-recovery bundle containing the supplied
PostgreSQL and file backups plus host configuration and recovery metadata.
USAGE
}

postgres_backup=""
files_backup=""
while (($#)); do
  case "$1" in
    --postgres) postgres_backup="${2:-}"; shift 2 ;;
    --files) files_backup="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unbekannte Option für Recovery-Backup: $1" ;;
  esac
done

[[ "$EUID" -eq 0 ]] || die "Recovery-Bundles mit Secrets benötigen root-Rechte."
require_command age
require_command python3
require_command tar
require_command sha256sum

postgres_backup="$(realpath "$postgres_backup")"
files_backup="$(realpath "$files_backup")"
[[ -f "$postgres_backup" ]] || die "PostgreSQL-Backup fehlt: $postgres_backup"
[[ -f "$files_backup" ]] || die "Datei-Backup fehlt: $files_backup"
verify_backup_checksum "$postgres_backup"
verify_backup_checksum "$files_backup"
key_fingerprints="$(python3 "$SCRIPT_DIR/backup_metadata.py" fingerprints "$ENV_FILE")"
python3 - "$key_fingerprints" <<'PY'
import json, sys
values = json.loads(sys.argv[1])
if not isinstance(values, list) or not values:
    raise SystemExit("Recovery backup requires a valid WEBHOOK_ENCRYPTION_KEYS key ring.")
PY

recipient="$(read_env BACKUP_AGE_RECIPIENT)"
[[ "$recipient" =~ ^age1[0-9a-z]{20,}$ ]] \
  || die "BACKUP_AGE_RECIPIENT fehlt oder ist kein age-Empfänger. Der private Schlüssel darf nur auf dem Backup-Gerät liegen."

backup_dir="$INFRA_DIR/data/backups/recovery"
run_dir="$INFRA_DIR/data/control/run"
install -d -m 0700 "$backup_dir"
install -d -m 0700 "$run_dir"
stage="$(mktemp -d "$run_dir/recovery-stage.XXXXXX")"
plain_bundle="$(mktemp "$run_dir/recovery-bundle.XXXXXX.tar.gz")"
cleanup() {
  rm -rf "$stage" "$plain_bundle"
}
trap cleanup EXIT
chmod 700 "$stage"
chmod 600 "$plain_bundle"

install -d -m 0700 \
  "$stage/artifacts/postgres" \
  "$stage/artifacts/files" \
  "$stage/configuration/backend-config" \
  "$stage/configuration/control-secrets" \
  "$stage/system"

install -m 0600 "$postgres_backup" "${postgres_backup}.sha256" "$stage/artifacts/postgres/"
if [[ -f "${postgres_backup}.restore.json" && -f "${postgres_backup}.restore.json.sha256" ]]; then
  install -m 0600 \
    "${postgres_backup}.restore.json" \
    "${postgres_backup}.restore.json.sha256" \
    "$stage/artifacts/postgres/"
fi
install -m 0600 "$files_backup" "${files_backup}.sha256" "$stage/artifacts/files/"
install -m 0600 "$ENV_FILE" "$stage/configuration/infrastructure.env"
python3 - "$stage/configuration/secret-keyring.json" "$key_fingerprints" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
fingerprints = json.loads(sys.argv[2])
path.write_text(json.dumps({
    "schema_version": 1,
    "secret_key_fingerprints": fingerprints,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
path.chmod(0o600)
PY

if [[ -f "$INFRA_DIR/first-run-credentials.txt" ]]; then
  install -m 0600 "$INFRA_DIR/first-run-credentials.txt" "$stage/configuration/first-run-credentials.txt"
fi
if [[ -f "$REPO_ROOT/frontend/.env" ]]; then
  install -m 0600 "$REPO_ROOT/frontend/.env" "$stage/configuration/frontend.env"
fi
while IFS= read -r -d '' cfg; do
  install -m 0600 "$cfg" "$stage/configuration/backend-config/$(basename "$cfg")"
done < <(find "$REPO_ROOT/backend/config" -maxdepth 1 -type f -name '*.cfg' -print0 | sort -z)

if [[ -d "$INFRA_DIR/data/control/secrets" ]]; then
  while IFS= read -r -d '' secret_file; do
    relative="${secret_file#"$INFRA_DIR/data/control/secrets/"}"
    target="$stage/configuration/control-secrets/$relative"
    install -d -m 0700 "$(dirname "$target")"
    install -m 0600 "$secret_file" "$target"
  done < <(
    find "$INFRA_DIR/data/control/secrets" -type f \
      ! -name 'database-restore-approval.json' -print0
  )
fi

if [[ -f /etc/os-release ]]; then
  install -m 0600 /etc/os-release "$stage/system/os-release"
fi
install -d -m 0700 "$stage/system/host-config"
for host_config in \
  /etc/fstab \
  /etc/hostname \
  /etc/hosts \
  /etc/docker/daemon.json \
  /etc/ssh/sshd_config \
  /etc/ufw/user.rules \
  /etc/ufw/user6.rules \
  /boot/firmware/config.txt \
  /boot/firmware/cmdline.txt; do
  if [[ -f "$host_config" ]]; then
    safe_name="${host_config#/}"
    safe_name="${safe_name//\//__}"
    install -m 0600 "$host_config" "$stage/system/host-config/$safe_name"
  fi
done
if [[ -d /etc/ssh/sshd_config.d ]]; then
  while IFS= read -r -d '' host_config; do
    install -m 0600 "$host_config" "$stage/system/host-config/sshd_config.d__$(basename "$host_config")"
  done < <(find /etc/ssh/sshd_config.d -maxdepth 1 -type f -print0)
fi
uname -a > "$stage/system/uname.txt"
systemctl list-unit-files --no-pager 2>/dev/null > "$stage/system/systemd-unit-files.txt" || true
dpkg-query -W -f='${binary:Package}\t${Version}\n' 2>/dev/null \
  > "$stage/system/packages.tsv" || true
docker version 2>/dev/null > "$stage/system/docker-version.txt" || true
docker compose version 2>/dev/null > "$stage/system/compose-version.txt" || true

version="$(cat "$REPO_ROOT/VERSION" 2>/dev/null || true)"
commit="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
remote_url="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || true)"
python3 - "$stage/system/backup-metadata.json" "$version" "$commit" "$remote_url" <<'PY'
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import socket
import sys

path = Path(sys.argv[1])
payload = {
    "version": sys.argv[2],
    "git_commit": sys.argv[3],
    "git_remote": sys.argv[4],
    "hostname": socket.gethostname(),
    "architecture": platform.machine(),
    "kernel": platform.release(),
    "created_at": datetime.now(timezone.utc).isoformat(),
}
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
find "$stage/system" -type d -exec chmod 0700 {} +
find "$stage/system" -type f -exec chmod 0600 {} +

python3 "$SCRIPT_DIR/recovery_bundle.py" create-manifest \
  "$stage" "$(basename "$postgres_backup")" "$(basename "$files_backup")"

tar -czf "$plain_bundle" -C "$stage" manifest.json artifacts configuration system

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="$backup_dir/rbf-recovery-${timestamp}.tar.gz.age"
temporary_output="${output}.part"
rm -f "$temporary_output"
age -r "$recipient" -o "$temporary_output" "$plain_bundle"
chmod 600 "$temporary_output"
mv "$temporary_output" "$output"
backup_finalize "$output" "recovery"

retention_days="$(read_env BACKUP_RETENTION_DAYS)"
retention_days="${retention_days:-14}"
find "$backup_dir" -type f -mtime "+$retention_days" -delete

export_dir="$(read_env BACKUP_PULL_EXPORT_DIR)"
export_user="$(read_env BACKUP_PULL_EXPORT_USER)"
if [[ -n "$export_dir" || -n "$export_user" ]]; then
  [[ -n "$export_dir" && -n "$export_user" ]] \
    || die "BACKUP_PULL_EXPORT_DIR und BACKUP_PULL_EXPORT_USER müssen gemeinsam gesetzt sein."
  [[ "$export_dir" == /* ]] || die "BACKUP_PULL_EXPORT_DIR muss absolut sein."
  id "$export_user" >/dev/null 2>&1 || die "BACKUP_PULL_EXPORT_USER existiert nicht: $export_user"
  export_group="$(id -gn "$export_user")"
  install -d -m 0700 -o "$export_user" -g "$export_group" "$export_dir"
  install -m 0600 -o "$export_user" -g "$export_group" "$output" "${output}.sha256" "$export_dir/"
  (
    cd "$export_dir"
    sha256sum -c "$(basename "${output}.sha256")" >/dev/null
  )
  find "$export_dir" -maxdepth 1 -type f \
    \( -name 'rbf-recovery-*.tar.gz.age' -o -name 'rbf-recovery-*.tar.gz.age.sha256' \) \
    -mtime "+$retention_days" -delete
  success "Verschlüsseltes Pull-Export wurde bereitgestellt: $export_dir/$(basename "$output")"
fi

if [[ -n "${BACKUP_RESULT_FILE:-}" ]]; then
  printf '%s\n' "$output" > "$BACKUP_RESULT_FILE"
  chmod 600 "$BACKUP_RESULT_FILE"
fi
success "Vollständiges verschlüsseltes Recovery-Bundle erstellt: $output"
