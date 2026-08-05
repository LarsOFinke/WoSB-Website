#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/quiet-gate.sh"

cd "$ROOT_DIR"
agent_run_quiet 'Infrastrukturverträge' bash infrastructure/scripts/quality/tests/infrastructure.sh
agent_run_quiet 'Update-/Releaseverträge' bash infrastructure/scripts/quality/tests/update-management.sh
agent_run_quiet 'Repository-Hygiene' python3 infrastructure/scripts/quality/check_repository.py --strict-tree
