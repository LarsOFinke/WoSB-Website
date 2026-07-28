#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"
source "$INFRA_DIR/scripts/lib/host/control.sh"

[[ "$EUID" -eq 0 ]] || die "Admin backup operations require root privileges."
require_command python3
require_command ssh
require_command sftp
require_command ssh-keyscan
require_command ssh-keygen
require_command flock

control_root="$INFRA_DIR/data/control"
inbox="$control_root/inbox/backup.request"
run_dir="$control_root/run"
claimed="$run_dir/backup.request.$$"
mkdir -p "$run_dir" "$control_root/status" "$control_root/secrets"
chown root:root "$run_dir" "$control_root/status" "$control_root/secrets"
chmod 700 "$run_dir" "$control_root/secrets"
chmod 755 "$control_root/status"

[[ -e "$inbox" ]] || exit 0

# Keep the request visible to the path unit while another update, restore or
# backup is active. It is claimed only after both global locks are held.
exec 8>"$run_dir/update.lock"
flock 8
exec 9>"$run_dir/backup.lock"
flock 9

[[ -e "$inbox" ]] || exit 0
rm -f "$claimed"
claim_control_request "$inbox" "$claimed" 10001
exec python3 "$INFRA_DIR/scripts/backup/backup-admin-runner.py" "$INFRA_DIR" "$claimed"
