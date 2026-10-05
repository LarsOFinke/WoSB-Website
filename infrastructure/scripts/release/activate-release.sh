#!/usr/bin/env bash
# Finish a freshly selected release or resume the same verified failed artifact.
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install_root="${1:?installation root required}"; version="${2:?version required}"
previous_release="${3:-}"; host_nginx_migration="${4:-false}"
[[ "$EUID" -eq 0 && "$install_root" == /* && "$install_root" != / && "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
shared="$install_root/shared"; release_dir="$install_root/releases/$version"
[[ "$(readlink -f "$install_root/current")" == "$release_dir" ]] || exit 2
deployment_record="$shared/deployments/$version.json"
artifact_copy="$shared/release-artifacts/rbf-deployment-$version.tar.gz"

RBF_SYSTEMD_INFRA_DIR="$install_root/current/infrastructure" \
  "$install_root/current/infrastructure/scripts/deployment/install-systemd.sh"
echo "[release] Restarting rbf-hub.service and waiting for Spring Boot/Compose."
# rbf-hub.service owns its complete startup deadline. Wrapping systemctl in a
# shorter timeout can cancel a healthy first activation while PostgreSQL is
# initializing, Flyway is migrating, or Spring is still inside its readiness
# budget.
systemctl restart rbf-hub.service
# The project gateway now binds loopback only. Public ports are available.
source "$SCRIPT_DIR/../lib/host/gateway-migration.sh"
activate_host_gateway "$host_nginx_migration"
echo "[release] Connecting the private gateway to host NGINX."
RBF_RUNTIME_INFRA_DIR="$install_root/current/infrastructure" /usr/bin/env bash -c '
  set -Eeuo pipefail
  source "$1/scripts/lib/env.sh"
  source "$1/scripts/lib/host/nginx.sh"
  configure_host_nginx
' _ "$install_root/current/infrastructure"
echo "[release] Running readiness and gateway smoke tests (max. 60 seconds)."
smoke_args=()
[[ -z "$previous_release" ]] && smoke_args+=(--bootstrap-login)
timeout 60s "$install_root/current/infrastructure/scripts/checks/smoke-test.sh" "${smoke_args[@]}"

if [[ -z "$previous_release" ]]; then
  RBF_RUNTIME_INFRA_DIR="$release_dir/infrastructure" /usr/bin/env bash -c '
    set -Eeuo pipefail
    source "$1/scripts/lib/env.sh"
    source "$1/scripts/lib/host/storage.sh"
    set_env_value SEED_ADMIN_PASSWORD ""
    materialize_runtime_secrets
  ' _ "$release_dir/infrastructure"
  echo "[release] Retired the bootstrap password from the persistent runtime environment."
fi

install -m 0600 "$artifact_copy" "$shared/release-artifacts/current.tar.gz"
(cd "$shared/release-artifacts" && sha256sum current.tar.gz > current.tar.gz.sha256)
printf '%s\n' "$version" > "$shared/current-version"
chmod 0644 "$shared/current-version"
# Publish global rollback metadata before marking the version active. If killed
# between these atomic writes, the version remains resumable as activating/failed.
python3 - "$deployment_record" "$shared/deployment-state.json" <<'PYRECORD'
import json, sys
from pathlib import Path
record = Path(sys.argv[1])
metadata = json.loads(record.read_text()); metadata["state"] = "active"
for destination in (Path(sys.argv[2]), record):
    temporary = destination.with_name("." + destination.name + ".tmp")
    temporary.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    temporary.chmod(0o600)
    temporary.replace(destination)
PYRECORD
