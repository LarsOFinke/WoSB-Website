#!/usr/bin/env bash
set -Eeuo pipefail
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/host/control.sh"
INSTALL_ROOT="${RBF_INSTALL_ROOT:-/srv/rbf}"
REQUEST="$INFRA_DIR/data/control/inbox/update.request"; STATUS="$INFRA_DIR/data/control/status/update-status.json"
RUN_DIR="$INFRA_DIR/data/control/run"; install -d -m 0700 "$RUN_DIR" "$(dirname "$STATUS")"
artifact=""; operation=""; requested_by="cli"
while (($#)); do
  case "$1" in --artifact) artifact="${2:-}"; shift 2;; --requested-by) requested_by="${2:-}"; shift 2;; --restart) operation=restart; shift;; --rollback) operation=rollback; shift;; -h|--help) echo "Usage: update.sh [--artifact FILE|--restart|--rollback] [--requested-by NAME]"; exit 0;; *) echo "Unknown option: $1" >&2; exit 2;; esac
done
exec 9>"$RUN_DIR/operation.lock"; flock 9
if [[ -z "$artifact" && -z "$operation" && -f "$REQUEST" ]]; then
  claimed="$RUN_DIR/update-request.$$.json"
  claim_control_request "$REQUEST" "$claimed" 10001
  mapfile -d '' -t request < <(python3 - "$claimed" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); print(p.get('operation','update'),end='\0'); print(p.get('requested_by','admin-panel'),end='\0')
PY
  )
  rm -f "$claimed"
  operation="${request[0]:-update}"; requested_by="${request[1]:-admin-panel}"
fi
operation="${operation:-update}"
write_status(){
  local state="$1" message="$2"
  STATE="$state" MESSAGE="$message" OPERATION="$operation" REQUESTED_BY="$requested_by" STATUS="$STATUS" python3 <<'PY'
import json,os
from datetime import datetime,timezone
from pathlib import Path
p=Path(os.environ['STATUS']); now=datetime.now(timezone.utc).isoformat()
old={}
try: old=json.loads(p.read_text())
except Exception: pass
payload={"state":os.environ['STATE'],"operation":os.environ['OPERATION'],"message":os.environ['MESSAGE'],"requested_by":os.environ['REQUESTED_BY'],"requested_at":old.get('requested_at') or now,"started_at":old.get('started_at') or now,"heartbeat_at":now if os.environ['STATE']=='running' else None,"finished_at":now if os.environ['STATE'] in {'succeeded','failed'} else None}
t=p.with_name('.'+p.name+'.tmp'); t.write_text(json.dumps(payload,indent=2)+'\n'); t.replace(p); p.chmod(0o644)
PY
}
write_status running "Host operation started."
trap 'write_status failed "Host operation failed."' ERR
case "$operation" in
  update)
    if [[ -z "$artifact" ]]; then
      artifact="$(find "$INSTALL_ROOT/shared/releases/inbox" -maxdepth 1 -type f -name 'rbf-deployment-*.tar.gz' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
    fi
    [[ -f "$artifact" && -f "$artifact.sha256" ]] || { echo "[update] No verified release artifact found in $INSTALL_ROOT/shared/releases/inbox." >&2; exit 1; }
    "$INFRA_DIR/scripts/release/install-artifact.sh" --artifact "$artifact" --checksum "$artifact.sha256" --install-root "$INSTALL_ROOT" --requested-by "$requested_by"
    ;;
  restart)
    exec 8>"$RUN_DIR/update.lock"; flock 8
    "$INFRA_DIR/scripts/services/restart-application.sh"
    ;;
  rollback) "$INFRA_DIR/scripts/release/rollback-release.sh";;
  *) echo "Unsupported operation: $operation" >&2; exit 2;;
esac
trap - ERR
write_status succeeded "Host operation completed successfully."
