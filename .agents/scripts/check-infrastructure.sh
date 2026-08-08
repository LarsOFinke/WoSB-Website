#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/quiet-gate.sh"

cd "$ROOT_DIR"
agent_run_quiet 'infrastructure contracts' bash infrastructure/scripts/quality/tests/infrastructure.sh
agent_run_quiet 'update/release contracts' bash infrastructure/scripts/quality/tests/update-management.sh
agent_run_quiet 'TLS/target-environment contracts' bash infrastructure/scripts/quality/tests/tls-environment-safety.sh
agent_run_quiet 'repository hygiene' python3 infrastructure/scripts/quality/check_repository.py --strict-tree
