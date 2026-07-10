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
DATABASE_URL=postgresql+psycopg://rbf:validation@postgres:5432/rbf
DB_SCHEMA_MODE=migrate
UPLOAD_DIR=/data/uploads
CORS_ORIGINS=https://royal-blackwater-fleet.eu
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
  RBF_ENV_FILE="$TMP_DIR/sqlite.env" PYTHONPATH=src alembic upgrade head
  RBF_ENV_FILE="$TMP_DIR/sqlite.env" PYTHONPATH=src alembic check
)

printf '\n[3/7] PostgreSQL offline migration rendering\n'
(
  cd "$ROOT_DIR/backend"
  RBF_ENV_FILE="$TMP_DIR/postgres.env" PYTHONPATH=src alembic upgrade head --sql > "$TMP_DIR/postgres-schema.sql"
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
  [[ -s src/assets/rbf-fleet-icon.png ]]
  grep -q "@/assets/rbf-fleet-icon.png" src/core/components/BrandLockup.vue
  npm run test:build-designer
  npm run check:locales
  npm run build
)

printf '\n[5/7] Shell and Compose syntax\n'
bash -n "$ROOT_DIR/setup.sh"
bash -n "$ROOT_DIR/update.sh"

# Entrypoints are invoked through bash throughout CI and internal delegation.
# Validate their shell contract instead of relying on filesystem mode bits,
# which may be lost in ZIPs, Windows worktrees or copied CI fixtures.
for entrypoint_script in \
  "$ROOT_DIR/setup.sh" \
  "$ROOT_DIR/update.sh" \
  "$ROOT_DIR/scripts/validate.sh" \
  "$ROOT_DIR/infrastructure/setup.sh"; do
  [[ -f "$entrypoint_script" ]] || {
    echo "[error] Missing shell entrypoint: $entrypoint_script" >&2
    exit 1
  }
  head -n 1 "$entrypoint_script" | grep -Eq '^#!/usr/bin/env bash$|^#!/bin/bash$' || {
    echo "[error] Invalid bash shebang: $entrypoint_script" >&2
    exit 1
  }
done

grep -q 'run: bash ./scripts/validate.sh' "$ROOT_DIR/.github/workflows/ci.yml"
while IFS= read -r file; do bash -n "$file"; done < <(find "$ROOT_DIR/infrastructure" "$ROOT_DIR/scripts" -type f -name '*.sh' -print | sort)
python - "$ROOT_DIR/infrastructure/compose.yml" "$ROOT_DIR/infrastructure/scripts/lib/docker.sh" "$ROOT_DIR/infrastructure/scripts/services/update.sh" <<'PY'
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
postgres = data["services"]["postgres"]
assert postgres.get("env_file") == [".env"], postgres.get("env_file")
assert "environment" not in postgres, postgres.get("environment")
postgres_healthcheck = postgres["healthcheck"]["test"][1]
assert "$${POSTGRES_USER}" in postgres_healthcheck, postgres_healthcheck
assert "$${POSTGRES_DB}" in postgres_healthcheck, postgres_healthcheck
seed_command = data["services"]["seed"]["command"][2]
assert "$$AUTO_SEED" in seed_command, seed_command
assert "./data/uploads:/data/uploads" in data["services"]["seed"].get("volumes", [])
gateway = data["services"]["gateway"]
assert "./data/acme:/var/www/certbot:ro" in gateway["volumes"]
api = data["services"]["api"]
assert api["image"].startswith("${RBF_API_IMAGE")
assert "./data/control:/run/rbf-control" in api.get("volumes", [])
assert api.get("environment", {}).get("CONTROL_DIR") == "/run/rbf-control"
assert gateway["image"].startswith("${RBF_GATEWAY_IMAGE")
assert gateway.get("build", {}).get("args", {}).get("VITE_MONITORING_HTTPS_PORT") == "${MONITORING_HTTPS_PORT:-8443}"
monitoring = data["services"]["monitoring-gateway"]
assert monitoring["profiles"] == ["monitoring"]
assert "${MONITORING_HTTPS_PORT:-8443}:443" in monitoring["ports"]
assert "./nginx/monitoring.conf:/etc/nginx/conf.d/default.conf:ro" in monitoring["volumes"]
assert monitoring["networks"] == ["frontend", "backend"], monitoring["networks"]
controller = Path(sys.argv[2]).read_text()
assert '--env-file "$ENV_FILE"' in controller
for variable in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "DATABASE_URL"):
    assert f"-u {variable}" in controller
steps = [
    'bw_compose up -d postgres',
    'bw_compose run --rm migrate',
    'bw_compose run --rm seed',
    'bw_compose up -d api',
    'bw_compose_with_profiles up -d --remove-orphans',
]
positions = [controller.index(step) for step in steps]
assert positions == sorted(positions), positions

update_controller = Path(sys.argv[3]).read_text()
assert 'RUN_MIGRATIONS=false' in update_controller
assert 'RUN_SEED=false' in update_controller
assert '--migrate)' in update_controller
assert '--seed)' in update_controller
assert '--no-auto-migrate)' in update_controller
assert 'backend/migrations/versions' in update_controller
assert 'backup-data.sh' in update_controller
assert 'backup-all.sh' in update_controller
assert 'deploy_stack' not in update_controller
assert 'deploy_application_update "$RUN_MIGRATIONS" "$RUN_SEED"' in update_controller
assert update_controller.index('ensure_monitoring_services') < update_controller.index('deploy_application_update "$RUN_MIGRATIONS" "$RUN_SEED"')

application_update = controller[controller.index('deploy_application_update()'):controller.index('deploy_stack()')]
assert 'bw_compose up -d --no-deps api' in application_update
assert 'bw_compose up -d --no-deps gateway' in application_update
assert 'ensure_monitoring_services' in application_update
assert 'bw_compose up -d postgres' in application_update
assert 'bw_compose run --rm migrate' in application_update
assert 'bw_compose run --rm seed' in application_update
PY

# Exercise the code-only deployment function with fake Compose hooks. The
# default path must not invoke PostgreSQL, migrations or seeding.
DB_SAFE_CALL_LOG="$TMP_DIR/db-safe-update.log"
(
  source "$ROOT_DIR/infrastructure/scripts/lib/docker.sh"
  ensure_env_file() { :; }
  read_env() { [[ "$1" == ENABLE_MONITORING ]] && printf 'false\n' || printf '\n'; }
  bw_compose() { printf '%s\n' "$*" >> "$DB_SAFE_CALL_LOG"; }
  bw_compose_with_profiles() { printf 'profile %s\n' "$*" >> "$DB_SAFE_CALL_LOG"; }
  wait_for_postgres() { printf 'wait-postgres\n' >> "$DB_SAFE_CALL_LOG"; }
  wait_for_api() { printf 'wait-api\n' >> "$DB_SAFE_CALL_LOG"; }
  deploy_application_update false false >/dev/null
)
grep -q '^up -d --no-deps api$' "$DB_SAFE_CALL_LOG"
grep -q '^up -d --no-deps gateway$' "$DB_SAFE_CALL_LOG"
! grep -Eq 'postgres|migrate|seed|wait-postgres' "$DB_SAFE_CALL_LOG"

DB_WRITE_CALL_LOG="$TMP_DIR/db-write-update.log"
(
  source "$ROOT_DIR/infrastructure/scripts/lib/docker.sh"
  ensure_env_file() { :; }
  read_env() {
    case "$1" in
      ENABLE_MONITORING) printf 'false\n' ;;
      POSTGRES_USER) printf 'rbf\n' ;;
      POSTGRES_DB) printf 'rbf\n' ;;
      *) printf '\n' ;;
    esac
  }
  bw_compose() { printf '%s\n' "$*" >> "$DB_WRITE_CALL_LOG"; }
  bw_compose_with_profiles() { printf 'profile %s\n' "$*" >> "$DB_WRITE_CALL_LOG"; }
  wait_for_postgres() { printf 'wait-postgres\n' >> "$DB_WRITE_CALL_LOG"; }
  wait_for_api() { printf 'wait-api\n' >> "$DB_WRITE_CALL_LOG"; }
  deploy_application_update true true >/dev/null
)
grep -q '^up -d postgres$' "$DB_WRITE_CALL_LOG"
grep -q '^run --rm migrate$' "$DB_WRITE_CALL_LOG"
grep -q '^run --rm seed$' "$DB_WRITE_CALL_LOG"
grep -q '^wait-postgres$' "$DB_WRITE_CALL_LOG"

for unit in rbf-hub.service rbf-hub-backup.service rbf-hub-backup.timer rbf-hub-cert-renew.service rbf-hub-cert-renew.timer rbf-hub-update.service rbf-hub-update.path; do
  [[ -f "$ROOT_DIR/infrastructure/systemd/$unit" ]]
done
[[ ! -e "$ROOT_DIR/infrastructure/systemd/rbv-hub.service" ]]
[[ ! -e "$ROOT_DIR/infrastructure/systemd/blackwater-hub.service" ]]
grep -q 'PathExists=@INFRA_DIR@/data/control/update.request' "$ROOT_DIR/infrastructure/systemd/rbf-hub-update.path"
grep -q 'update-from-admin.sh' "$ROOT_DIR/infrastructure/systemd/rbf-hub-update.service"
grep -q 'flock -n' "$ROOT_DIR/infrastructure/scripts/services/update.sh"
! grep -R -q '/var/run/docker.sock' "$ROOT_DIR/backend" "$ROOT_DIR/infrastructure/compose.yml"
grep -q '/.well-known/acme-challenge/' "$ROOT_DIR/infrastructure/nginx/default.conf"
grep -q 'certbot renew' "$ROOT_DIR/infrastructure/scripts/tls/renew-certificate.sh"
grep -q 'CERTIFICATE_PROVIDER letsencrypt' "$ROOT_DIR/infrastructure/scripts/tls/sync-certificate.sh"

if docker compose version >/dev/null 2>&1; then
  if [[ ! -f "$ROOT_DIR/infrastructure/.env" ]]; then
    cp "$ROOT_DIR/infrastructure/.env.example" "$ROOT_DIR/infrastructure/.env"
    INFRA_ENV_CREATED=true
  fi
  (cd "$ROOT_DIR/infrastructure" && docker compose -f compose.yml config >/dev/null)
fi

printf '\n[6/7] First-run bootstrap simulation\n'
cp -a "$ROOT_DIR/infrastructure" "$TMP_DIR/infrastructure"
# Reproduce CI/filesystem checkouts that do not preserve the executable bit.
# The simulation must still work because setup is invoked through bash.
chmod 0644 "$TMP_DIR/infrastructure/setup.sh"
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
  [[ -z "${POSTGRES_USER:-}" ]] || exit 91
  [[ -z "${POSTGRES_PASSWORD:-}" ]] || exit 92
  [[ -z "${POSTGRES_DB:-}" ]] || exit 93
  [[ -z "${DATABASE_URL:-}" ]] || exit 94
  [[ " $* " == *" --env-file "* ]] || exit 95
  exit 0
fi
exit 0
FAKE_DOCKER
chmod +x "$TMP_DIR/fake-bin/docker"
POSTGRES_USER=poisoned-user \
POSTGRES_PASSWORD=poisoned-password \
POSTGRES_DB=poisoned-database \
DATABASE_URL=postgresql+psycopg://poisoned \
PATH="$TMP_DIR/fake-bin:$PATH" bash "$TMP_DIR/infrastructure/setup.sh" \
  --skip-host \
  --no-start \
  --profile full \
  --hostname rbf-validation.local \
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
grep -q '^CONTROL_DIR=/run/rbf-control$' "$TMP_DIR/infrastructure/.env"
grep -q '^COMPOSE_PROJECT_NAME=rbf-hub$' "$TMP_DIR/infrastructure/.env"
grep -q '^APP_HOSTNAME=rbf-validation.local$' "$TMP_DIR/infrastructure/.env"
grep -q '^TLS_MODE=auto$' "$TMP_DIR/infrastructure/.env"
grep -q '^CERTIFICATE_PROVIDER=self-signed$' "$TMP_DIR/infrastructure/.env"
grep -q '^LETSENCRYPT_CERT_NAME=rbf-validation.local$' "$TMP_DIR/infrastructure/.env"
grep -q '^DATABASE_URL=postgresql+psycopg://' "$TMP_DIR/infrastructure/.env"
grep -q '^Admin user: validation-admin$' "$TMP_DIR/infrastructure/first-run-credentials.txt"
openssl x509 -in "$TMP_DIR/infrastructure/data/certs/fullchain.pem" -noout -ext subjectAltName \
  | grep -q 'DNS:rbf-validation.local, IP Address:192.0.2.10'

# Simulate rerunning setup against the legacy/current root-level PostgreSQL
# cluster layout. Existing database files must remain untouched.
printf '16\n' > "$TMP_DIR/infrastructure/data/postgres/PG_VERSION"
printf 'preserve-me\n' > "$TMP_DIR/infrastructure/data/postgres/EXISTING_DATA_SENTINEL"
touch "$TMP_DIR/infrastructure/data/postgres/.gitkeep"
sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=rbv-hub/' "$TMP_DIR/infrastructure/.env"
POSTGRES_USER=poisoned-user \
POSTGRES_PASSWORD=poisoned-password \
POSTGRES_DB=poisoned-database \
DATABASE_URL=postgresql+psycopg://poisoned \
PATH="$TMP_DIR/fake-bin:$PATH" bash "$TMP_DIR/infrastructure/setup.sh" \
  --skip-host \
  --no-start \
  --profile full \
  --hostname rbf-validation.local \
  --ip 192.0.2.10 \
  --admin-username validation-admin \
  --admin-display-name 'Validation Commander' >/dev/null
[[ ! -e "$TMP_DIR/infrastructure/data/postgres/.gitkeep" ]]
[[ "$(cat "$TMP_DIR/infrastructure/data/postgres/PG_VERSION")" == 16 ]]
[[ "$(cat "$TMP_DIR/infrastructure/data/postgres/EXISTING_DATA_SENTINEL")" == preserve-me ]]
grep -q '^COMPOSE_PROJECT_NAME=rbf-hub$' "$TMP_DIR/infrastructure/.env"

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

# Runtime data directories are created and owned by setup.sh/container UIDs.
# Keeping tracked marker files inside them makes git pull/reset fail after setup.
if git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git -C "$ROOT_DIR" ls-files 'infrastructure/data/**' | grep -q .; then
    echo "[error] Runtime files under infrastructure/data must not be tracked by Git." >&2
    git -C "$ROOT_DIR" ls-files 'infrastructure/data/**' >&2
    exit 1
  fi
fi

printf '\nAll validation checks passed.\n'
