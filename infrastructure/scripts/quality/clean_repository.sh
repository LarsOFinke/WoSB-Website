#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
MODE="${1:-generated}"
[[ "$MODE" == generated || "$MODE" == --all ]] || { echo 'Usage: infrastructure/scripts/quality/clean_repository.sh [--all]' >&2; exit 2; }
for path in frontend/dist frontend/coverage frontend/src/locales/generated spring-api/target release; do rm -rf "$ROOT_DIR/$path"; done
[[ "$MODE" != --all ]] || rm -rf "$ROOT_DIR/frontend/node_modules" "$ROOT_DIR/.venv"
find "$ROOT_DIR" -type d \( -name .git -o -name node_modules \) -prune -o -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache -o -name .tox -o -name .nox -o -name htmlcov \) -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR" -type d \( -name .git -o -name node_modules \) -prune -o -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '.coverage*' \) -exec rm -f {} +
printf 'Repository-Artefakte bereinigt.\n'
