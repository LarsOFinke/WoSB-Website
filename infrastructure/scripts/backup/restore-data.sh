#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

components=(uploads certs letsencrypt uptime-kuma)
backup_file=""
while (($#)); do
  case "$1" in
    --yes) shift ;;
    --components)
      [[ -n "${2:-}" ]] || die "--components benötigt eine kommagetrennte Modulliste."
      IFS=',' read -r -a components <<<"$2"
      shift 2
      ;;
    --*) die "Unbekannte Restore-Option: $1" ;;
    *) [[ -z "$backup_file" ]] || die "Nur ein Datei-Backup darf angegeben werden."; backup_file="$1"; shift ;;
  esac
done
[[ -n "$backup_file" ]] || die "Aufruf: $0 --yes [--components uploads,certs,letsencrypt,uptime-kuma] /pfad/rbf-files-*.tar.gz"
backup_file="$(realpath "$backup_file")"
[[ -f "$backup_file" ]] || die "Backup nicht gefunden: $backup_file"
verify_backup_checksum "$backup_file"

declare -A selected=()
for component in "${components[@]}"; do
  [[ "$component" =~ ^(uploads|certs|letsencrypt|uptime-kuma)$ ]] || die "Nicht unterstütztes Restore-Modul: $component"
  selected["$component"]=1
done
(( ${#selected[@]} > 0 )) || die "Mindestens ein Restore-Modul muss ausgewählt werden."

python3 - "$backup_file" <<'PY'
from pathlib import PurePosixPath
import sys
import tarfile

archive = sys.argv[1]
allowed = {"uploads", "certs", "letsencrypt", "uptime-kuma"}
with tarfile.open(archive, mode="r:gz") as handle:
    for member in handle.getmembers():
        path = PurePosixPath(member.name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or path.parts[0] not in allowed
        ):
            raise SystemExit(f"Unsicherer Pfad im Backup: {member.name}")
        if not (member.isdir() or member.isfile()):
            raise SystemExit(
                f"Nicht unterstützter Link oder Spezialdateityp im Backup: {member.name}"
            )
PY

tar_args=(--no-same-owner --no-same-permissions)
for component in "${!selected[@]}"; do tar_args+=("$component"); done
warn "Ausgewählte Restore-Module (${!selected[*]}) werden aus $backup_file wiederhergestellt."
tar -xzf "$backup_file" -C "$INFRA_DIR/data" "${tar_args[@]}"
success "Datei-Wiederherstellung abgeschlossen. Führe anschließend setup/doctor und einen Smoke-Test aus."
