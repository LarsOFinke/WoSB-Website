#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
created_env=false

cleanup() {
  [[ "$created_env" != true ]] || rm -f "$FRONTEND_DIR/.env"
}
trap cleanup EXIT

if [[ ! -f "$FRONTEND_DIR/.env" ]]; then
  cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
  created_env=true
fi

(cd "$FRONTEND_DIR" && npm run test:ci)
