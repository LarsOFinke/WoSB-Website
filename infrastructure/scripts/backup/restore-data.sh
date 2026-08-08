#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

components=(uploads certs letsencrypt)
backup_file=""
while (($#)); do
  case "$1" in
    --yes) shift ;;
    --components)
      [[ -n "${2:-}" ]] || die "--components requires a comma-separated module list."
      IFS=',' read -r -a components <<<"$2"
      shift 2
      ;;
    --*) die "Unknown restore option: $1" ;;
    *) [[ -z "$backup_file" ]] || die "Only one file backup may be specified."; backup_file="$1"; shift ;;
  esac
done
[[ -n "$backup_file" ]] || die "Usage: $0 --yes [--components uploads,certs,letsencrypt] /path/rbf-files-*.tar.gz"
backup_file="$(realpath "$backup_file")"
[[ -f "$backup_file" ]] || die "Backup not found: $backup_file"
verify_backup_checksum "$backup_file"

declare -A selected=()
for component in "${components[@]}"; do
  [[ "$component" =~ ^(uploads|certs|letsencrypt)$ ]] || die "Unsupported restore module: $component"
  selected["$component"]=1
done
(( ${#selected[@]} > 0 )) || die "At least one restore module must be selected."

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
            raise SystemExit(f"Unsafe path in backup: {member.name}")
        if not (member.isdir() or member.isfile()):
            raise SystemExit(
                f"Unsupported link or special-file type in backup: {member.name}"
            )
PY

restore_components=()
for component in "${!selected[@]}"; do
  if tar -tzf "$backup_file" | awk -v component="$component" '$0 == component || index($0, component "/") == 1 {found=1} END {exit !found}'; then
    restore_components+=("$component")
  elif [[ "$component" == uploads ]]; then
    die "Required module is missing from the file backup: $component"
  else
    warn "Restore module is missing from the backup and will be skipped: $component"
  fi
done
(( ${#restore_components[@]} > 0 )) || die "None of the selected restore modules is present in the backup."

stage="$(mktemp -d "$INFRA_DIR/data/.restore-stage.XXXXXX")"
cleanup() { rm -rf -- "$stage"; }
trap cleanup EXIT
tar_args=(--no-same-owner --no-same-permissions)
for component in "${restore_components[@]}"; do tar_args+=("$component"); done
warn "Selected restore modules (${restore_components[*]}) will be restored from $backup_file."
tar -xzf "$backup_file" -C "$stage" "${tar_args[@]}"
for component in "${restore_components[@]}"; do
  target="$INFRA_DIR/data/$component"
  [[ ! -L "$target" ]] || die "Restore target is an unsafe symlink: $target"
  [[ -d "$stage/$component" ]] || die "Restore module was not extracted: $component"
  rm -rf -- "$target"
  mv -- "$stage/$component" "$target"
done
success "File restore completed. Run setup/doctor and a smoke test afterward."
