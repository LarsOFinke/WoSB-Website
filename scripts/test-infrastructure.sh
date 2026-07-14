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

python3 - "$INFRA_DIR/compose.yml" <<'PY_COMPOSE'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
api_section = text.split("  api:\n", 1)[1].split("\n  gateway:\n", 1)[0]
networks_section = text.split("\nnetworks:\n", 1)[1]
assert "      - backend\n      - outbound\n" in api_section, "API must retain database isolation and outbound egress"
assert "  backend:\n    driver: bridge\n    internal: true\n" in networks_section, "backend network must remain internal"
assert "  outbound:\n    driver: bridge\n" in networks_section, "outbound network must be defined"
PY_COMPOSE

if docker compose version >/dev/null 2>&1; then
  cp "$INFRA_DIR/.env.example" "$INFRA_DIR/.env"
  trap 'rm -f "$INFRA_DIR/.env"' EXIT
  (cd "$INFRA_DIR" && docker compose -f compose.yml config >/dev/null)
fi

echo "Infrastructure checks OK."

grep -q "limit_req_zone.*auth_login" "$ROOT_DIR/infrastructure/nginx/default.conf"
grep -q "Content-Security-Policy" "$ROOT_DIR/infrastructure/nginx/default.conf"

grep -q 'RBF_DISCORD_BOT_BIND_HOST:-0.0.0.0' "$INFRA_DIR/scripts/services/manage-discord-bot.sh"
grep -q 'RBF_DISCORD_BOT_FIREWALL_MODE:-auto' "$INFRA_DIR/scripts/services/configure-discord-bot-gateway.sh"
grep -q 'ufw allow from "$subnet" to "$HOST_GATEWAY_IP" port "$BOT_PORT"' "$INFRA_DIR/scripts/services/configure-discord-bot-gateway.sh"
grep -q 'http://host.docker.internal:${BOT_PORT}/health' "$INFRA_DIR/scripts/services/configure-discord-bot-gateway.sh"
! grep -q 'ufw allow 8765/tcp' "$INFRA_DIR/scripts/services/configure-discord-bot-gateway.sh"
grep -q 'proxy_pass http://host.docker.internal:8765/webhooks/rbf;' "$INFRA_DIR/nginx/default.conf"
