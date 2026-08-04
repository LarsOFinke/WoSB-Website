#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

components=(uploads certs letsencrypt)
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
[[ -n "$backup_file" ]] || die "Aufruf: $0 --yes [--components uploads,certs,letsencrypt] /pfad/rbf-files-*.tar.gz"
backup_file="$(realpath "$backup_file")"
[[ -f "$backup_file" ]] || die "Backup nicht gefunden: $backup_file"
verify_backup_checksum "$backup_file"

declare -A selected=()
for component in "${components[@]}"; do
  [[ "$component" =~ ^(uploads|certs|letsencrypt)$ ]] || die "Nicht unterstütztes Restore-Modul: $component"
  selected["$component"]=1
done
(( ${#selected[@]} > 0 )) || die "Mindestens ein Restore-Modul muss ausgewählt werden."

python3 - "$backup_file" <<'PY'
from pathlib import PurePosixPath
import sys
import tarfile

archive = sys.argv[1]
allowed = {"uploads", "certs", "letsencrypt"}
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

restore_components=()
for component in "${!selected[@]}"; do
  if tar -tzf "$backup_file" | awk -v component="$component" '$0 == component || index($0, component "/") == 1 {found=1} END {exit !found}'; then
    restore_components+=("$component")
  elif [[ "$component" == uploads ]]; then
    die "Pflichtmodul fehlt im Datei-Backup: $component"
  else
    warn "Restore-Modul fehlt im Backup und wird übersprungen: $component"
  fi
done
(( ${#restore_components[@]} > 0 )) || die "Kein ausgewähltes Restore-Modul ist im Backup enthalten."

stage="$(mktemp -d "$INFRA_DIR/data/.restore-stage.XXXXXX")"
cleanup() { rm -rf -- "$stage"; }
trap cleanup EXIT
tar_args=(--no-same-owner --no-same-permissions)
for component in "${restore_components[@]}"; do tar_args+=("$component"); done
warn "Ausgewählte Restore-Module (${restore_components[*]}) werden aus $backup_file wiederhergestellt."
tar -xzf "$backup_file" -C "$stage" "${tar_args[@]}"
for component in "${restore_components[@]}"; do
  target="$INFRA_DIR/data/$component"
  [[ ! -L "$target" ]] || die "Restore-Ziel ist ein unsicherer Symlink: $target"
  [[ -d "$stage/$component" ]] || die "Restore-Modul wurde nicht extrahiert: $component"
  rm -rf -- "$target"
  mv -- "$stage/$component" "$target"
done
success "Datei-Wiederherstellung abgeschlossen. Führe anschließend setup/doctor und einen Smoke-Test aus."
