#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec /usr/bin/env bash "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh" "$@"
