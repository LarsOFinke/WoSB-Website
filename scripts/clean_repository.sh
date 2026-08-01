#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:-generated}"
[[ "$MODE" == "generated" || "$MODE" == "--all" ]] || {
  echo "Usage: scripts/clean_repository.sh [--all]" >&2
  exit 2
}

remove_dir() {
  local path="$1"
  [[ -e "$path" ]] || return 0
  printf 'Entferne %s\n' "${path#"$ROOT_DIR/"}"
  rm -rf -- "$path"
}

# Authored source never lives in these locations.
for path in \
  "$ROOT_DIR/frontend/dist" \
  "$ROOT_DIR/frontend/coverage" \
  "$ROOT_DIR/frontend/src/locales/generated" \
  "$ROOT_DIR/tools/linux/recovery-tool/build" \
  "$ROOT_DIR/tools/linux/recovery-tool/dist" \
  "$ROOT_DIR/tools/windows/recovery-tool/build" \
  "$ROOT_DIR/tools/windows/recovery-tool/dist" \
  "$ROOT_DIR/release"; do
  remove_dir "$path"
done

# In all-mode remove dependency trees before scanning caches inside them.
if [[ "$MODE" == "--all" ]]; then
  for path in \
    "$ROOT_DIR/frontend/node_modules" \
    "$ROOT_DIR/backend/.venv" \
    "$ROOT_DIR/.venv" \
    "$ROOT_DIR/tools/linux/recovery-tool/.venv-build" \
    "$ROOT_DIR/tools/windows/recovery-tool/.venv-build"; do
    remove_dir "$path"
  done
fi

while IFS= read -r -d '' path; do
  remove_dir "$path"
done < <(
  find "$ROOT_DIR" \
    \( -type d \( -name .git -o -name node_modules -o -name .venv -o -name .venv-build \) -prune \) -o \
    \( -type d \( \
      -name __pycache__ -o \
      -name .pytest_cache -o \
      -name .mypy_cache -o \
      -name .ruff_cache -o \
      -name .tox -o \
      -name .nox -o \
      -name htmlcov \
    \) -print0 \)
)

while IFS= read -r -d '' path; do
  rm -f -- "$path"
done < <(
  find "$ROOT_DIR" \
    \( -type d \( -name .git -o -name node_modules -o -name .venv -o -name .venv-build \) -prune \) -o \
    \( -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '.coverage' -o -name '.coverage.*' \) -print0 \)
)

printf 'Repository-Artefakte bereinigt.\n'
