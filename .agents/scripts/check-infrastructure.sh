#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/quiet-gate.sh"

cd "$ROOT_DIR"
agent_run_quiet 'Infrastrukturverträge' bash scripts/test-infrastructure.sh
agent_run_quiet 'Update-/Releaseverträge' bash scripts/test-update-management.sh
agent_run_quiet 'Repository-Hygiene' python3 scripts/check_repository.py --strict-tree
