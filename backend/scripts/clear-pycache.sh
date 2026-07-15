#!/usr/bin/env bash
set -Eeuo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

find "$BACKEND_DIR" -type d \
  \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.ruff_cache' -o -name '.mypy_cache' \) \
  -prune -exec rm -rf {} +
find "$BACKEND_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

printf 'Python caches cleared in %s\n' "$BACKEND_DIR"
