#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
/usr/bin/env bash "$SCRIPT_DIR/backup-postgres.sh"
/usr/bin/env bash "$SCRIPT_DIR/backup-data.sh"
