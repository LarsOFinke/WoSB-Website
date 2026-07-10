#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/env.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"

ensure_env_file
cert_name="$(read_env LETSENCRYPT_CERT_NAME)"
[[ -n "$cert_name" ]] || cert_name="$(read_env APP_HOSTNAME)"
lineage="${RENEWED_LINEAGE:-$CERTBOT_CONFIG_DIR/live/$cert_name}"
[[ -s "$lineage/fullchain.pem" && -s "$lineage/privkey.pem" ]] || die "Let's-Encrypt-Zertifikat nicht gefunden: $lineage"

install -m 0644 "$lineage/fullchain.pem" "$INFRA_DIR/data/certs/fullchain.pem"
install -m 0600 "$lineage/privkey.pem" "$INFRA_DIR/data/certs/privkey.pem"
set_env_value CERTIFICATE_PROVIDER letsencrypt

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if [[ -n "$(bw_compose ps -q gateway 2>/dev/null || true)" ]]; then
    bw_compose exec -T gateway nginx -s reload >/dev/null 2>&1 || bw_compose restart gateway >/dev/null
  fi
  if is_true "$(read_env ENABLE_MONITORING)" && [[ -n "$(bw_compose_with_profiles ps -q monitoring-gateway 2>/dev/null || true)" ]]; then
    bw_compose_with_profiles exec -T monitoring-gateway nginx -s reload >/dev/null 2>&1 \
      || bw_compose_with_profiles restart monitoring-gateway >/dev/null
  fi
fi
success "Let's-Encrypt-Zertifikat wurde installiert und die Gateways wurden neu geladen."
