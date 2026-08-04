#!/usr/bin/env bash
set -Eeuo pipefail

HOST_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOST_LIB_DIR/env.sh"
source "$HOST_LIB_DIR/host/packages.sh"
source "$HOST_LIB_DIR/host/storage.sh"
source "$HOST_LIB_DIR/host/firewall.sh"
source "$HOST_LIB_DIR/host/tls.sh"
