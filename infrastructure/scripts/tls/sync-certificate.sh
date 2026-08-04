#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/env.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"

ensure_env_file
cert_name="$(read_env LETSENCRYPT_CERT_NAME)"
[[ -n "$cert_name" ]] || cert_name="$(read_env APP_HOSTNAME)"
lineage="${RENEWED_LINEAGE:-$CERTBOT_CONFIG_DIR/live/$cert_name}"
[[ -s "$lineage/fullchain.pem" && -s "$lineage/privkey.pem" ]] || die "Let's-Encrypt-Zertifikat nicht gefunden: $lineage"

certificate_dir="$INFRA_DIR/data/certs"
temporary_fullchain="$(mktemp "$certificate_dir/.fullchain.pem.XXXXXX")"
temporary_privkey="$(mktemp "$certificate_dir/.privkey.pem.XXXXXX")"
cleanup_temporary() {
  rm -f "$temporary_fullchain" "$temporary_privkey"
}
trap cleanup_temporary EXIT
install -m 0644 "$lineage/fullchain.pem" "$temporary_fullchain"
install -o 0 -g 101 -m 0640 "$lineage/privkey.pem" "$temporary_privkey"
mv -fT "$temporary_fullchain" "$certificate_dir/fullchain.pem"
mv -fT "$temporary_privkey" "$certificate_dir/privkey.pem"
set_env_value CERTIFICATE_PROVIDER letsencrypt

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if [[ -n "$(bw_compose ps -q gateway 2>/dev/null || true)" ]]; then
    bw_compose exec -T gateway nginx -s reload >/dev/null 2>&1 || bw_compose restart gateway >/dev/null
  fi
fi
success "Let's-Encrypt-Zertifikat wurde installiert und die Gateways wurden neu geladen."
