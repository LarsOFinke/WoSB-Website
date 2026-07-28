#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"
require_command flock

run_dir="$INFRA_DIR/data/control/run"
mkdir -p "$run_dir"
update_lock="$run_dir/update.lock"
expected_update_lock="$(realpath -m "$update_lock")"
inherited_update_lock=""
if [[ -e "/proc/$$/fd/9" ]]; then
  inherited_target="$(readlink -f "/proc/$$/fd/9" 2>/dev/null || true)"
  if [[ "$inherited_target" == "$expected_update_lock" ]] && flock -n 9; then
    inherited_update_lock=true
  fi
fi

if [[ "$inherited_update_lock" != true ]]; then
  exec 8>"$update_lock"
  flock 8
fi
exec 7>"$run_dir/backup.lock"
flock 7

/usr/bin/env bash "$SCRIPT_DIR/backup-postgres.sh"
/usr/bin/env bash "$SCRIPT_DIR/backup-data.sh"
