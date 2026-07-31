#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

[[ "$EUID" -eq 0 ]] || die "Das Zusammenführen von Verschlüsselungsschlüsseln benötigt root-Rechte."
[[ $# -eq 1 ]] || die "Aufruf: sudo $0 /pfad/zur/alten-infrastructure.env"
require_command python3
source_env="$(realpath "$1")"
[[ -f "$source_env" ]] || die "Quell-.env nicht gefunden: $source_env"
ensure_env_file

backup_env="$INFRA_DIR/.env.before-keyring-merge-$(date -u +%Y%m%dT%H%M%SZ)"
install -m 0600 "$ENV_FILE" "$backup_env"

python3 - "$ENV_FILE" "$source_env" <<'PY'
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import shutil
import sys

current_path = Path(sys.argv[1])
source_path = Path(sys.argv[2])


def read_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized = value.strip()
        if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {'"', "'"}:
            normalized = normalized[1:-1]
        values[key.strip()] = normalized
    return values


def valid_fernet_key(value: str) -> bool:
    try:
        decoded = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (UnicodeEncodeError, ValueError):
        return False
    return len(decoded) == 32


def explicit_keys(values: dict[str, str]) -> list[str]:
    return [
        key
        for key in (item.strip() for item in values.get("WEBHOOK_ENCRYPTION_KEYS", "").split(","))
        if key and valid_fernet_key(key)
    ]


def legacy_derived_key(values: dict[str, str]) -> str | None:
    database_url = values.get("DATABASE_URL", "")
    if not database_url:
        return None
    material = f"royal-blackwater-fleet:webhooks:v1:{database_url}".encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(material).digest()).decode("ascii")


current_values = read_values(current_path)
source_values = read_values(source_path)
current_keys = explicit_keys(current_values)
source_keys = explicit_keys(source_values)
if not source_keys:
    legacy = legacy_derived_key(source_values)
    if legacy:
        source_keys = [legacy]
if not current_keys:
    raise SystemExit("Current environment has no valid WEBHOOK_ENCRYPTION_KEYS primary key.")
if not source_keys:
    raise SystemExit("Source environment has no recoverable encryption key material.")

merged = list(current_keys)
for key in source_keys:
    if key not in merged:
        merged.append(key)

lines = current_path.read_text(encoding="utf-8").splitlines()
replacement = "WEBHOOK_ENCRYPTION_KEYS=" + ",".join(merged)
for index, line in enumerate(lines):
    if line.startswith("WEBHOOK_ENCRYPTION_KEYS="):
        lines[index] = replacement
        break
else:
    lines.append(replacement)

staged = current_path.with_name(".env.keyring-merge.tmp")
staged.write_text("\n".join(lines) + "\n", encoding="utf-8")
staged.chmod(0o600)
shutil.move(staged, current_path)
current_path.chmod(0o600)
print(f"Encryption key ring merged safely; active key count: {len(merged)}")
PY

success "Verschlüsselungsschlüssel wurden ohne Ausgabe der Schlüsselwerte zusammengeführt."
warn "Sicherung der vorherigen .env: $backup_env"
warn "API anschließend mit 'docker compose ... up -d --force-recreate api' neu erstellen."
