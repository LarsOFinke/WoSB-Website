#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
fail(){ echo "[tls-safety] $*" >&2; exit 1; }
for command in openssl grep; do
  command -v "$command" >/dev/null 2>&1 || fail "missing baseline command: $command"
done
real_openssl="$(command -v openssl)"

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

# Some OpenSSL versions historically reported a hostname mismatch in output while
# still returning status 0. Simulate that behavior so validation must fail closed
# based on the positive match result, not only the process exit status.
mkdir -p "$work/bin"
cat > "$work/bin/openssl" <<'WRAPPER'
#!/usr/bin/env bash
set -u
if [[ " $* " == *" x509 "* && " $* " == *" -checkhost "* ]]; then
  output="$($REAL_OPENSSL "$@" 2>&1)"
  printf '%s\n' "$output"
  exit 0
fi
exec "$REAL_OPENSSL" "$@"
WRAPPER
chmod +x "$work/bin/openssl"
if (
  export REAL_OPENSSL="$real_openssl"
  export PATH="$work/bin:$PATH"
  INFRA_DIR="$ROOT_DIR/infrastructure"
  source "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
  source "$ROOT_DIR/infrastructure/scripts/lib/host/tls.sh"
  verify_tls_material "$work/cert.pem" "$work/key.pem" production.example.org 3600
) >/dev/null 2>&1; then
  fail 'hostname mismatch was accepted when OpenSSL returned status 0'
fi

grep -Fq -- 'Production requires TLS_MODE=letsencrypt' "$ROOT_DIR/infrastructure/scripts/lib/env.sh" || fail 'production TLS mode is not enforced'
grep -Fq -- "Production must never use Let's Encrypt staging" "$ROOT_DIR/infrastructure/scripts/lib/env.sh" || fail 'production staging is not rejected'
grep -Eq -- '--target-environment.*target_environment' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh" || fail 'origin target is not forwarded to website setup'
grep -Fq -- 'verify_tls_material' "$ROOT_DIR/infrastructure/scripts/tls/sync-certificate.sh" || fail 'certificate swap bypasses validation'
grep -Fq -- 'Finalize public production TLS within the atomic activation' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh" || fail 'production TLS is outside activation rollback boundary'
! grep -Eq -- '127\.0\.0\.1:.*5432' "$ROOT_DIR/infrastructure/compose.release.yml" || fail 'release PostgreSQL still publishes a host port'
printf '[tls-safety] OK: target isolation, certificate validation and release DB exposure\n'
