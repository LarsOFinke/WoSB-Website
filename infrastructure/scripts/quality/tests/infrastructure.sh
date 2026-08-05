#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
INFRA_DIR="$ROOT_DIR/infrastructure"

fail(){ printf '[infrastructure] %s\n' "$*" >&2; exit 1; }
for command in bash python3; do command -v "$command" >/dev/null || fail "missing command: $command"; done

while IFS= read -r -d '' file; do bash -n "$file"; done < <(
  find "$ROOT_DIR" -type d \( -name .git -o -name node_modules -o -name target -o -name dist -o -name data \) -prune -o -type f -name '*.sh' -print0
)
while IFS= read -r -d '' file; do python3 -m py_compile "$file"; done < <(
  find "$INFRA_DIR/scripts" "$ROOT_DIR/tests" -type d -name __pycache__ -prune -o -type f -name '*.py' -print0
)
python3 - "$INFRA_DIR/compose.yml" "$INFRA_DIR/compose.release.yml" <<'PY'
import re,sys
from pathlib import Path
for raw in sys.argv[1:]:
    path=Path(raw); text=path.read_text()
    service_block=re.split(r'(?m)^networks:\s*$',text,maxsplit=1)[0]
    services=set(re.findall(r'(?m)^  ([A-Za-z0-9_-]+):\n',service_block))
    required={'postgres','api','gateway'}
    if not required <= services: raise SystemExit(f'{path}: missing {sorted(required-services)}')
    forbidden={'secure-api','migrate','seed'} & services
    if forbidden: raise SystemExit(f'{path}: legacy services {sorted(forbidden)}')
    for service in ('api','gateway'):
        match=re.search(rf'(?ms)^  {service}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)',text)
        section=match.group(1) if match else ''
        for token in ('read_only: true','no-new-privileges:true','cap_drop: [ALL]'):
            if token not in section: raise SystemExit(f'{path}: {service} missing {token}')
        if service == 'gateway' and 'group_add: ["10001"]' not in section:
            raise SystemExit(f'{path}: gateway cannot traverse the shared control status directory')
PY

[[ ! -d "$ROOT_DIR/backend" ]] || fail 'Python backend directory still exists'
for token in FASTAPI_INTERNAL_URL RBF_SECURE_API_IMAGE AUTO_SEED; do
  ! grep -R --exclude-dir=data --exclude-dir=.git --exclude-dir=generation --exclude-dir=quality -- "$token" "$INFRA_DIR" >/dev/null \
    || fail "legacy runtime token: $token"
done
[[ -f "$INFRA_DIR/docker/api-runtime.Dockerfile" ]] || fail 'missing API runtime image'
[[ -f "$INFRA_DIR/docker/gateway-runtime.Dockerfile" ]] || fail 'missing gateway runtime image'
if grep -Eq '^[[:space:]]*/?artifacts/?[[:space:]]*$' "$ROOT_DIR/.dockerignore"; then
  fail 'release artifacts are excluded from the runtime image build context'
fi
[[ -x "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh" ]] || fail 'artifact installer is not executable'
[[ -x "$ROOT_DIR/infrastructure/scripts/release/setup_website.sh" ]] || fail 'website setup wrapper is not executable'
[[ -x "$ROOT_DIR/infrastructure/scripts/release/cleanup-failed-release.sh" ]] || fail 'failed-release cleanup is not executable'
[[ -x "$ROOT_DIR/infrastructure/scripts/services/systemd-stop.sh" ]] || fail 'systemd stop helper is not executable'
grep -q 'ExecStop=/usr/bin/env bash @INFRA_DIR@/scripts/services/systemd-stop.sh' "$INFRA_DIR/systemd/rbf-hub.service" \
  || fail 'systemd service must preserve failed-start containers for diagnostics'
if find "$INFRA_DIR/scripts" -type f -name '*.sh' ! -perm /111 -print -quit | grep -q .; then
  fail 'infrastructure shell scripts must be executable'
fi
[[ -f "$INFRA_DIR/scripts/migration/verify-alembic-head.sql" && -f "$INFRA_DIR/scripts/migration/adopt-flyway.sql" ]] || fail 'controlled legacy schema adoption gate missing'
python3 "$INFRA_DIR/scripts/quality/check_documentation.py" --cache-only

runtime_root="$(mktemp -d)"
runtime_override="$runtime_root/releases/1.0.3/infrastructure"
mkdir -p "$runtime_override" "$runtime_root/shared/data"
ln -s "$runtime_root/shared/data" "$runtime_override/data"
resolved_override="$(RBF_RUNTIME_INFRA_DIR="$runtime_override" bash -c 'source "$1"; printf "%s" "$INFRA_DIR"' _ "$INFRA_DIR/scripts/lib/common.sh")"
[[ "$resolved_override" == "$(realpath "$runtime_override")" ]] || fail 'incoming release helpers cannot bind to the active runtime infrastructure'
manifest_root="$(RBF_RUNTIME_INFRA_DIR="$runtime_override" RBF_INSTALL_ROOT="$runtime_root" bash -c 'source "$1"; backup_manifest_root' _ "$INFRA_DIR/scripts/backup/common.sh")"
[[ "$manifest_root" == "$(realpath "$runtime_root")" ]] || fail 'versioned release backup manifest root does not resolve to the installation root'
rm -rf -- "$runtime_root"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  temp_env="$(mktemp)"; trap 'rm -f "$temp_env"' EXIT
  cp "$INFRA_DIR/.env.example" "$temp_env"
  RBF_ENV_FILE="$temp_env" docker compose --env-file "$temp_env" -f "$INFRA_DIR/compose.release.yml" config >/dev/null
fi
bash "$ROOT_DIR/infrastructure/scripts/quality/tests/debug-diagnostics.sh"
printf '[infrastructure] OK: shell, Python, Compose and artifact-runtime invariants\n'
