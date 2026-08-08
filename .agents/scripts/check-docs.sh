#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/quiet-gate.sh"

cd "$ROOT_DIR"
agent_run_quiet 'documentation links and commands' python3 infrastructure/scripts/quality/check_documentation.py
agent_run_quiet 'agent module cache' bash .agents/scripts/check-cache.sh
agent_run_quiet 'generated docs and repository hygiene' python3 infrastructure/scripts/quality/check_repository.py --strict-tree
