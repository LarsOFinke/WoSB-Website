#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python "$ROOT_DIR/scripts/check_repository.py"
bash "$ROOT_DIR/scripts/test.sh" full

echo "Validation completed successfully."
