#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin"
touch "$work/identity"
cat > "$work/origin.env" <<EOF
RBF_DEPLOY_HOST=target.example
RBF_DEPLOY_USER=rbfadmin
RBF_DEPLOY_PORT=2222
RBF_DEPLOY_IDENTITY_FILE=$work/identity
RBF_DEPLOY_INSTALL_ROOT=/srv/rbf
EOF
cat > "$work/bin/ssh" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" > "$RBF_TEST_SSH_ARGS"
cat >/dev/null
printf '%s\n' \
  '2026-08-05T10:24:56Z api | request started' \
  'api | api_error status=500 path=/api/calendar/events?start=private@example.org client=203.0.113.9' \
  'api | owner=private@example.org' \
  'api | peer=2001:db8::42' \
  'api | Authorization: Bearer secret-value Cookie=session-secret'
EOF
chmod +x "$work/bin/ssh"
PATH="$work/bin:$PATH" RBF_TEST_SSH_ARGS="$work/ssh.args" \
  bash "$ROOT_DIR/infrastructure/scripts/diagnostics/debug.sh" \
  --config "$work/origin.env" --area calendar --category http-500 --since 15m --tail 20 \
  --match calendar --output "$work/result.log" >/dev/null
grep -q 'api_error status=500' "$work/result.log"
grep -q 'target_environment=test' "$work/result.log"
grep -q '<redacted-ip>' "$work/result.log"
grep -q '<redacted-email>' "$work/result.log"
grep -q 'start=<redacted>' "$work/result.log"
grep -q '2026-08-05T10:24:56Z' "$work/result.log"
if grep -q '203.0.113.9\|2001:db8::42\|private@example.org\|secret-value\|session-secret' "$work/result.log"; then
  echo '[diagnostics-test] sensitive fixture value was not redacted' >&2; exit 1
fi
grep -q 'BatchMode=yes' "$work/ssh.args"
grep -q 'IdentitiesOnly=yes' "$work/ssh.args"
grep -q -- '--area calendar' "$work/ssh.args"
grep -q -- '--install-root /srv/rbf' "$work/ssh.args"
bash "$ROOT_DIR/infrastructure/scripts/diagnostics/collect-remote.sh" --help >/dev/null
if bash "$ROOT_DIR/infrastructure/scripts/diagnostics/collect-remote.sh" \
  --install-root /srv/rbf --area invalid >/dev/null 2>&1; then
  echo '[diagnostics-test] invalid area was accepted' >&2; exit 1
fi
printf '[diagnostics-test] OK: origin SSH, bounds and redaction\n'
