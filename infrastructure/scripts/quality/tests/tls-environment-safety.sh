#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
fail(){ echo "[tls-safety] $*" >&2; exit 1; }
for command in openssl grep; do
  command -v "$command" >/dev/null 2>&1 || fail "missing baseline command: $command"
done

# Functional certificate/key/hostname check.
openssl req -x509 -nodes -newkey rsa:2048 -days 30 \
  -subj '/CN=test.example.org' -addext 'subjectAltName=DNS:test.example.org' \
  -keyout "$work/key.pem" -out "$work/cert.pem" >/dev/null 2>&1
(
  INFRA_DIR="$ROOT_DIR/infrastructure"
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$ROOT_DIR/infrastructure/scripts/lib/host/tls.sh"
  verify_tls_material "$work/cert.pem" "$work/key.pem" test.example.org 3600
) || fail 'valid certificate material was rejected'
if (
  INFRA_DIR="$ROOT_DIR/infrastructure"
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$ROOT_DIR/infrastructure/scripts/lib/host/tls.sh"
  verify_tls_material "$work/cert.pem" "$work/key.pem" production.example.org 3600
) >/dev/null 2>&1; then
  fail 'hostname mismatch was accepted'
fi

grep -Fq -- 'Production requires TLS_MODE=letsencrypt' "$ROOT_DIR/infrastructure/scripts/lib/env.sh" || fail 'production TLS mode is not enforced'
grep -Fq -- "Production must never use Let's Encrypt staging" "$ROOT_DIR/infrastructure/scripts/lib/env.sh" || fail 'production staging is not rejected'
grep -Eq -- '--target-environment.*target_environment' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh" || fail 'origin target is not forwarded to website setup'
grep -Fq -- 'verify_tls_material' "$ROOT_DIR/infrastructure/scripts/tls/sync-certificate.sh" || fail 'certificate swap bypasses validation'
grep -Fq -- 'Finalize public production TLS within the atomic activation' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh" || fail 'production TLS is outside activation rollback boundary'
! grep -Eq -- '127\.0\.0\.1:.*5432' "$ROOT_DIR/infrastructure/compose.release.yml" || fail 'release PostgreSQL still publishes a host port'
printf '[tls-safety] OK: target isolation, certificate validation and release DB exposure\n'
