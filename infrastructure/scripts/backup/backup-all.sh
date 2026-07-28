#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"
require_command flock

run_dir="$INFRA_DIR/data/control/run"
mkdir -p "$run_dir"
exec 8>"$run_dir/update.lock"
flock 8
exec 9>"$run_dir/backup.lock"
flock 9

/usr/bin/env bash "$SCRIPT_DIR/backup-postgres.sh"
/usr/bin/env bash "$SCRIPT_DIR/backup-data.sh"
