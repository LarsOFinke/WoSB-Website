#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infrastructure"

affected=("$ROOT_DIR/setup.sh" "$ROOT_DIR/update.sh")
while IFS= read -r file; do affected+=("$file"); done < <(find "$ROOT_DIR/infrastructure" "$ROOT_DIR/scripts" -type f -name '*.sh' -print | sort)
for file in "${affected[@]}"; do bash -n "$file"; done

[[ ! -e "$ROOT_DIR/backend/.env" ]]
[[ ! -e "$ROOT_DIR/frontend/.env" ]]
[[ ! -e "$INFRA_DIR/.env" ]]
! grep -R -q '/var/run/docker.sock' "$ROOT_DIR/backend" "$INFRA_DIR/compose.yml"
grep -q 'update_migrate)' "$INFRA_DIR/scripts/services/update.sh"
grep -q 'update_migrate_seed)' "$INFRA_DIR/scripts/services/update.sh"
grep -q 'flock -n' "$INFRA_DIR/scripts/services/update.sh"
grep -q 'data/postgres/PG_VERSION' "$INFRA_DIR/setup.sh"
grep -q 'AUTO_SEED=true rbf-seed' "$INFRA_DIR/compose.yml"
grep -q '^AUTO_SEED=false$' "$INFRA_DIR/.env.example"

if docker compose version >/dev/null 2>&1; then
  cp "$INFRA_DIR/.env.example" "$INFRA_DIR/.env"
  trap 'rm -f "$INFRA_DIR/.env"' EXIT
  (cd "$INFRA_DIR" && docker compose -f compose.yml config >/dev/null)
fi

echo "Infrastructure checks OK."

grep -q "limit_req_zone.*auth_login" "$ROOT_DIR/infrastructure/nginx/default.conf"
grep -q "Content-Security-Policy" "$ROOT_DIR/infrastructure/nginx/default.conf"
