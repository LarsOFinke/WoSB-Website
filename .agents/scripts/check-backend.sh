#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/quiet-gate.sh"

cd "$ROOT_DIR"
agent_run_quiet 'SQL-Runtime-Audit' python3 infrastructure/scripts/quality/audit_sql_runtime.py
agent_run_quiet 'Spring-/PostgreSQL-Tests' make spring-test
