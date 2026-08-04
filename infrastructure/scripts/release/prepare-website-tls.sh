#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
target_env="${1:?target environment path required}"
target_shared="${2:?target shared directory required}"
source "$INFRA_DIR/scripts/lib/env.sh"
source "$INFRA_DIR/scripts/lib/host/tls.sh"
export ENV_FILE="$target_env"
INFRA_DIR="$target_shared"
cert_dir="$INFRA_DIR/data/certs"
mkdir -p "$cert_dir"
if [[ ! -s "$cert_dir/fullchain.pem" || ! -s "$cert_dir/privkey.pem" ]]; then
  generate_self_signed_certificate
else
  chmod 0644 "$cert_dir/fullchain.pem"
  chown 0:101 "$cert_dir/privkey.pem"
  chmod 0640 "$cert_dir/privkey.pem"
fi
