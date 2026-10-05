#!/usr/bin/env bash
# Called with the installer's release lock held, after incoming artifact verification.
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install_root="${1:?installation root required}"; version="${2:?version required}"
manifest="${3:?verified manifest required}"; checksum="${4:?artifact checksum required}"
[[ "$EUID" -eq 0 ]] || { echo '[resume] Root privileges are required.' >&2; exit 1; }
metadata="$(mktemp)"
trap 'rm -f "$metadata"' EXIT
# Do not hide verifier failure in a process substitution/mapfile exit status.
python3 "$SCRIPT_DIR/verify-release-resume.py" "$install_root" "$version" "$manifest" "$checksum" > "$metadata"
mapfile -d '' -t values < "$metadata"
previous_release="${values[0]}"; host_nginx_migration="${values[1]}"
source "$SCRIPT_DIR/../lib/host/gateway-migration.sh"
preflight_host_gateway "$host_nginx_migration"
runtime="$install_root/current/infrastructure"
record="$install_root/shared/deployments/$version.json"
install -d -m 0700 "$install_root/shared/data/control/run"
exec 8>"$install_root/shared/data/control/run/update.lock"; flock 8
INFRA_DIR="$runtime"
source "$runtime/scripts/lib/maintenance.sh"
maintenance_enable update 300
resume_failed() {
  local code=$?
  trap - ERR
  python3 - "$record" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]); record = json.loads(p.read_text()); record["state"] = "failed"
temporary = p.with_suffix(".tmp"); temporary.write_text(json.dumps(record, indent=2) + "\n")
temporary.chmod(0o600); temporary.replace(p)
PY
  maintenance_disable failed 'Activation retry failed; fix the reported cause and rerun the same artifact.' || true
  echo '[resume] The selected release, original backup and rollback metadata were retained. Fix the error and retry the same artifact.' >&2
  exit "$code"
}
trap resume_failed ERR
echo '[resume] Resuming the verified selected release; retaining the original pre-deployment backup.'
"$SCRIPT_DIR/activate-release.sh" "$install_root" "$version" "$previous_release" "$host_nginx_migration"
maintenance_disable succeeded 'Release activation retry completed successfully.'
trap - ERR
echo "[resume] Activated Royal Blackwater Fleet $version."
