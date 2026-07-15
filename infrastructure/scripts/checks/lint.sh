#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"

require_command bash
require_command python3

log "Prüfe Bash-Syntax."
while IFS= read -r -d '' script; do
  bash -n "$script"
done < <(find "$INFRA_DIR" \
  -path "$INFRA_DIR/data" -prune -o \
  -path "$INFRA_DIR/.git" -prune -o \
  -type f -name '*.sh' -print0)

log "Prüfe Python-Syntax."
python3 - "$INFRA_DIR/scripts/discord-bot/apply-configuration.py" <<'PY'
import ast
from pathlib import Path
import sys

path = Path(sys.argv[1])
ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
PY

success "Statische Infrastruktur-Prüfungen erfolgreich."
