#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
FRONTEND_ENV_CREATED=false
INFRA_ENV_CREATED=false

cleanup() {
  rm -rf "$TMP_DIR"
  [[ "$FRONTEND_ENV_CREATED" == true ]] && rm -f "$ROOT_DIR/frontend/.env"
  [[ "$INFRA_ENV_CREATED" == true ]] && rm -f "$ROOT_DIR/infrastructure/.env"
  return 0
}
trap cleanup EXIT

cat > "$TMP_DIR/sqlite.env" <<ENV
APP_ENV=development
DATABASE_URL=sqlite:///$TMP_DIR/validation.db
DB_SCHEMA_MODE=none
UPLOAD_DIR=$TMP_DIR/uploads
CORS_ORIGINS=http://localhost
SESSION_COOKIE_SECURE=false
AUTO_SEED=false
ENV

cat > "$TMP_DIR/postgres.env" <<'ENV'
APP_ENV=production
DATABASE_URL=postgresql+psycopg://blackwater:validation@postgres:5432/blackwater
DB_SCHEMA_MODE=migrate
UPLOAD_DIR=/data/uploads
CORS_ORIGINS=https://blackwater.example
SESSION_COOKIE_SECURE=true
AUTO_SEED=false
ENV

printf '\n[1/7] Backend tests\n'
(
  cd "$ROOT_DIR/backend"
  PYTHONPATH=src pytest -q
  python -m compileall -q src migrations tests
)

printf '\n[2/7] SQLite Alembic lifecycle\n'
(
  cd "$ROOT_DIR/backend"
  BLACKWATER_ENV_FILE="$TMP_DIR/sqlite.env" PYTHONPATH=src alembic upgrade head
  BLACKWATER_ENV_FILE="$TMP_DIR/sqlite.env" PYTHONPATH=src alembic check
)

printf '\n[3/7] PostgreSQL offline migration rendering\n'
(
  cd "$ROOT_DIR/backend"
  BLACKWATER_ENV_FILE="$TMP_DIR/postgres.env" PYTHONPATH=src alembic upgrade head --sql > "$TMP_DIR/postgres-schema.sql"
  grep -q 'CREATE TABLE users' "$TMP_DIR/postgres-schema.sql"
  grep -q 'CREATE TABLE alembic_version' "$TMP_DIR/postgres-schema.sql"
)

printf '\n[4/7] Frontend locales and build\n'
if [[ ! -f "$ROOT_DIR/frontend/.env" ]]; then
  cp "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env"
  FRONTEND_ENV_CREATED=true
fi
(
  cd "$ROOT_DIR/frontend"
  npm run check:locales
  npm run build
)

printf '\n[5/7] Shell and Compose syntax\n'
bash -n "$ROOT_DIR/setup.sh"
while IFS= read -r file; do bash -n "$file"; done < <(find "$ROOT_DIR/infrastructure" "$ROOT_DIR/scripts" -type f -name '*.sh' -print | sort)
python - "$ROOT_DIR/infrastructure/compose.yml" "$ROOT_DIR/infrastructure/scripts/lib/docker.sh" <<'PY'
from pathlib import Path
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(0)
data = yaml.safe_load(Path(sys.argv[1]).read_text())
required = {"postgres", "migrate", "seed", "api", "gateway", "uptime-kuma", "monitoring-gateway"}
missing = required.difference(data["services"])
assert not missing, missing
seed_command = data["services"]["seed"]["command"][2]
assert "$$AUTO_SEED" in seed_command, seed_command
monitoring = data["services"]["monitoring-gateway"]
assert monitoring["profiles"] == ["monitoring"]
assert "${MONITORING_HTTPS_PORT:-8443}:443" in monitoring["ports"]
assert "./nginx/monitoring.conf:/etc/nginx/conf.d/default.conf:ro" in monitoring["volumes"]
controller = Path(sys.argv[2]).read_text()
steps = [
    'bw_compose up -d postgres',
    'bw_compose run --rm migrate',
    'bw_compose run --rm seed',
    'bw_compose up -d api',
    'bw_compose_with_profiles up -d --remove-orphans',
]
positions = [controller.index(step) for step in steps]
assert positions == sorted(positions), positions
PY

if docker compose version >/dev/null 2>&1; then
  if [[ ! -f "$ROOT_DIR/infrastructure/.env" ]]; then
    cp "$ROOT_DIR/infrastructure/.env.example" "$ROOT_DIR/infrastructure/.env"
    INFRA_ENV_CREATED=true
  fi
  (cd "$ROOT_DIR/infrastructure" && docker compose -f compose.yml config >/dev/null)
fi

printf '\n[6/7] First-run bootstrap simulation\n'
cp -a "$ROOT_DIR/infrastructure" "$TMP_DIR/infrastructure"
rm -f "$TMP_DIR/infrastructure/.env" \
      "$TMP_DIR/infrastructure/first-run-credentials.txt" \
      "$TMP_DIR/infrastructure/data/certs/fullchain.pem" \
      "$TMP_DIR/infrastructure/data/certs/privkey.pem"
# Simulate an update from the affected alpha package. Setup must remove only
# the legacy marker and leave the fresh PostgreSQL directory empty.
mkdir -p "$TMP_DIR/infrastructure/data/postgres"
touch "$TMP_DIR/infrastructure/data/postgres/.gitkeep"
mkdir -p "$TMP_DIR/fake-bin"
cat > "$TMP_DIR/fake-bin/docker" <<'FAKE_DOCKER'
#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${1:-}" == compose && "${2:-}" == version ]]; then
  exit 0
fi
if [[ "${1:-}" == compose ]]; then
  exit 0
fi
exit 0
FAKE_DOCKER
chmod +x "$TMP_DIR/fake-bin/docker"
PATH="$TMP_DIR/fake-bin:$PATH" "$TMP_DIR/infrastructure/setup.sh" \
  --skip-host \
  --no-start \
  --profile full \
  --hostname blackwater-validation.local \
  --ip 192.0.2.10 \
  --admin-username validation-admin \
  --admin-display-name 'Validation Commander' >/dev/null
[[ "$(stat -c '%a' "$TMP_DIR/infrastructure/.env")" == 600 ]]
[[ "$(stat -c '%a' "$TMP_DIR/infrastructure/first-run-credentials.txt")" == 600 ]]
[[ "$(stat -c '%a' "$TMP_DIR/infrastructure/data/certs/privkey.pem")" == 600 ]]
[[ ! -e "$TMP_DIR/infrastructure/data/postgres/.gitkeep" ]]
[[ -z "$(find "$TMP_DIR/infrastructure/data/postgres" -mindepth 1 -maxdepth 1 -print -quit)" ]]
grep -q '^APP_ENV=production$' "$TMP_DIR/infrastructure/.env"
grep -q '^DB_SCHEMA_MODE=migrate$' "$TMP_DIR/infrastructure/.env"
grep -q '^MONITORING_HTTPS_PORT=8443$' "$TMP_DIR/infrastructure/.env"
grep -q '^DATABASE_URL=postgresql+psycopg://' "$TMP_DIR/infrastructure/.env"
grep -q '^Admin user: validation-admin$' "$TMP_DIR/infrastructure/first-run-credentials.txt"
openssl x509 -in "$TMP_DIR/infrastructure/data/certs/fullchain.pem" -noout -ext subjectAltName \
  | grep -q 'DNS:blackwater-validation.local, IP Address:192.0.2.10'

# Simulate rerunning setup against the legacy/current root-level PostgreSQL
# cluster layout. Existing database files must remain untouched.
printf '16\n' > "$TMP_DIR/infrastructure/data/postgres/PG_VERSION"
printf 'preserve-me\n' > "$TMP_DIR/infrastructure/data/postgres/EXISTING_DATA_SENTINEL"
touch "$TMP_DIR/infrastructure/data/postgres/.gitkeep"
PATH="$TMP_DIR/fake-bin:$PATH" "$TMP_DIR/infrastructure/setup.sh" \
  --skip-host \
  --no-start \
  --profile full \
  --hostname blackwater-validation.local \
  --ip 192.0.2.10 \
  --admin-username validation-admin \
  --admin-display-name 'Validation Commander' >/dev/null
[[ ! -e "$TMP_DIR/infrastructure/data/postgres/.gitkeep" ]]
[[ "$(cat "$TMP_DIR/infrastructure/data/postgres/PG_VERSION")" == 16 ]]
[[ "$(cat "$TMP_DIR/infrastructure/data/postgres/EXISTING_DATA_SENTINEL")" == preserve-me ]]

if [[ "$FRONTEND_ENV_CREATED" == true ]]; then
  rm -f "$ROOT_DIR/frontend/.env"
  FRONTEND_ENV_CREATED=false
fi
if [[ "$INFRA_ENV_CREATED" == true ]]; then
  rm -f "$ROOT_DIR/infrastructure/.env"
  INFRA_ENV_CREATED=false
fi

printf '\n[7/7] Secret/artifact guard\n'
! find "$ROOT_DIR" \
  \( -path '*/node_modules' -o -path '*/dist' -o -path '*/.pytest_cache' -o -path '*/__pycache__' \) -prune -o \
  -type f \( -name '.env' -o -name '*.db' -o -name 'first-run-credentials.txt' -o -name 'privkey.pem' -o -name 'fullchain.pem' \) -print \
  | grep -q . || {
    echo 'Generated secrets, certificates or databases are present in the repository tree.' >&2
    exit 1
  }

printf '\nAll validation checks passed.\n'
