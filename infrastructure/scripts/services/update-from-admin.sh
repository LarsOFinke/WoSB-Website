#!/usr/bin/env bash
set -Eeuo pipefail
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec /usr/bin/env bash "$INFRA_DIR/scripts/services/update.sh" --requested-by admin-panel
