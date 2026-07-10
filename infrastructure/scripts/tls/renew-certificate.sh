#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

ensure_env_file
[[ "$(read_env CERTIFICATE_PROVIDER)" == letsencrypt ]] || exit 0
require_command certbot

certbot renew \
  --non-interactive \
  --config-dir "$CERTBOT_CONFIG_DIR" \
  --work-dir "$CERTBOT_WORK_DIR" \
  --logs-dir "$CERTBOT_LOGS_DIR" \
  --deploy-hook "$INFRA_DIR/scripts/tls/sync-certificate.sh"
