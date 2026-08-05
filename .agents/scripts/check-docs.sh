#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/quiet-gate.sh"

cd "$ROOT_DIR"
agent_run_quiet 'Dokumentationslinks und Befehle' python3 infrastructure/scripts/quality/check_documentation.py
agent_run_quiet 'Agenten-Modulcache' bash .agents/scripts/check-cache.sh
agent_run_quiet 'generierte Doku und Repository-Hygiene' python3 infrastructure/scripts/quality/check_repository.py --strict-tree
