#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-quick}"
[[ "$MODE" == quick || "$MODE" == full ]] || {
  echo "Usage: scripts/test.sh [quick|full]" >&2
  exit 2
}

tmp_dir=""
frontend_env_created=false
cleanup() {
  [[ "$frontend_env_created" == false ]] || rm -f "$ROOT_DIR/frontend/.env"
  [[ -z "$tmp_dir" ]] || rm -rf "$tmp_dir"
  rm -rf \
    "$ROOT_DIR/frontend/dist" \
    "$ROOT_DIR/frontend/src/locales/generated"
  "$ROOT_DIR/backend/scripts/clear-pycache.sh" >/dev/null 2>&1 || true
  find "$ROOT_DIR/tools/recovery-tool" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
}
trap cleanup EXIT

printf '\n[backend] lint and isolated tests\n'
(
  cd "$ROOT_DIR/backend"
  ruff check --no-cache src tests
  python "$ROOT_DIR/scripts/run_backend_tests.py"
)

printf '\n[recovery tool] unit tests\n'
python -m pytest -q -p no:cacheprovider "$ROOT_DIR/tools/recovery-tool/tests"

printf '\n[security] offline repository audit\n'
python "$ROOT_DIR/scripts/security_audit.py"

printf '\n[css] architecture audit\n'
python "$ROOT_DIR/scripts/audit_css.py"

printf '\n[frontend] deterministic checks\n'
(cd "$ROOT_DIR/frontend" && npm run test)

[[ "$MODE" == full ]] || exit 0

printf '\n[backend] baseline schema lifecycle\n'
tmp_dir="$(mktemp -d)"
cat > "$tmp_dir/test.env" <<ENV
APP_ENV=development
DATABASE_URL=sqlite:///$tmp_dir/test.db
DB_SCHEMA_MODE=none
UPLOAD_DIR=$tmp_dir/uploads
CONTROL_DIR=$tmp_dir/control
CORS_ORIGINS=http://localhost
SESSION_COOKIE_SECURE=false
AUTO_SEED=false
ENV
(
  cd "$ROOT_DIR/backend"
  PYTHONPATH=src python -m compileall -q src tests migrations
  RBF_ENV_FILE="$tmp_dir/test.env" PYTHONPATH=src alembic upgrade head
  RBF_ENV_FILE="$tmp_dir/test.env" PYTHONPATH=src alembic check
  RBF_ENV_FILE="$tmp_dir/test.env" PYTHONPATH=src alembic downgrade base
  RBF_ENV_FILE="$tmp_dir/test.env" PYTHONPATH=src alembic upgrade head
)

printf '\n[frontend] production build\n'
if [[ ! -f "$ROOT_DIR/frontend/.env" ]]; then
  cp "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env"
  frontend_env_created=true
fi
(cd "$ROOT_DIR/frontend" && npm run build)

printf '\n[infrastructure] static and Compose checks\n'
bash "$ROOT_DIR/scripts/test-infrastructure.sh"

"$ROOT_DIR/backend/scripts/clear-pycache.sh"
python "$ROOT_DIR/scripts/check_repository.py" --strict-tree
printf '\nValidation completed successfully.\n'
