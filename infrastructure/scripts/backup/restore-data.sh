#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[[ $# -eq 2 && "$1" == "--yes" ]] || die "Aufruf: $0 --yes /pfad/rbf-files-*.tar.gz"
backup_file="$(realpath "$2")"
[[ -f "$backup_file" ]] || die "Backup nicht gefunden: $backup_file"
verify_backup_checksum "$backup_file"

python3 - "$backup_file" <<'PY'
from pathlib import PurePosixPath
import sys
import tarfile

archive = sys.argv[1]
allowed = {"uploads", "certs", "uptime-kuma"}
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

warn "Uploads, Zertifikate und Uptime-Kuma-Daten werden aus $backup_file wiederhergestellt."
tar -xzf "$backup_file" -C "$INFRA_DIR/data" --no-same-owner --no-same-permissions
success "Datei-Wiederherstellung abgeschlossen. Führe anschließend setup/doctor und einen Smoke-Test aus."
