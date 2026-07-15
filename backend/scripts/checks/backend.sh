#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
python -m compileall -q src tests migrations
PYTHONPATH=src pytest --collect-only -q >/dev/null
printf 'Backend syntax and test collection checks passed.\n'
