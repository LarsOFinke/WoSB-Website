#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode="${1:-quick}"
[[ "$mode" == quick || "$mode" == full ]] || { echo "Usage: scripts/test.sh [quick|full]" >&2; exit 2; }

printf '\n[backend] lint and tests\n'
(
  cd "$ROOT_DIR/backend"
  ruff check --no-cache src tests
  python "$ROOT_DIR/scripts/run_backend_tests.py"
)

printf '\n[frontend] deterministic checks\n'
(
  cd "$ROOT_DIR/frontend"
  npm run test
)

if [[ "$mode" == full ]]; then
  printf '\n[backend] compile and migration lifecycle\n'
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  cat > "$tmp_dir/test.env" <<ENV
APP_ENV=development
DATABASE_URL=sqlite:///$tmp_dir/test.db
DB_SCHEMA_MODE=none
UPLOAD_DIR=$tmp_dir/uploads
CORS_ORIGINS=http://localhost
SESSION_COOKIE_SECURE=false
AUTO_SEED=false
ENV
  (
    cd "$ROOT_DIR/backend"
    PYTHONPATH=src python -m compileall -q src tests migrations
    RBF_ENV_FILE="$tmp_dir/test.env" PYTHONPATH=src alembic upgrade head
    RBF_ENV_FILE="$tmp_dir/test.env" PYTHONPATH=src alembic check
  )
  python "$ROOT_DIR/scripts/test_v1_data_migration.py"

  printf '\n[frontend] production build\n'
  frontend_env_created=false
  if [[ ! -f "$ROOT_DIR/frontend/.env" ]]; then
    cp "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env"
    frontend_env_created=true
  fi
  (cd "$ROOT_DIR/frontend" && npm run build)
  [[ "$frontend_env_created" == false ]] || rm -f "$ROOT_DIR/frontend/.env"
  rm -rf "$ROOT_DIR/frontend/dist"

  # compileall and test discovery create local caches that are not part of the source tree.
  find "$ROOT_DIR/backend" "$ROOT_DIR/scripts" -type d \
    \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache \) \
    -prune -exec rm -rf {} +
  find "$ROOT_DIR/backend" "$ROOT_DIR/scripts" -type f \
    \( -name '*.pyc' -o -name '*.pyo' \) -delete

  printf '\n[infrastructure] static and Compose checks\n'
  bash "$ROOT_DIR/scripts/test-infrastructure.sh"
  python "$ROOT_DIR/scripts/check_repository.py"
fi
