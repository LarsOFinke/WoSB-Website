#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
RESTORE="$ROOT_DIR/infrastructure/scripts/migration/restore-builds-from-origin.sh"
REMOTE="$ROOT_DIR/infrastructure/scripts/migration/restore-builds-remote.sh"
fail() { printf '[build-restore-test] %s\n' "$*" >&2; exit 1; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin"
touch "$work/identity"
chmod 0600 "$work/identity"
cat > "$work/origin.env" <<EOF
RBF_DEPLOY_HOST=build-restore.example.test
RBF_DEPLOY_USER=rbfadmin
RBF_DEPLOY_PORT=2222
RBF_DEPLOY_IDENTITY_FILE=$work/identity
RBF_DEPLOY_INSTALL_ROOT=/srv/rbf
EOF
chmod 0600 "$work/origin.env"

cat > "$work/bin/scp" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$RBF_BUILD_RESTORE_TEST_LOG"
EOF
cat > "$work/bin/ssh" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$RBF_BUILD_RESTORE_TEST_LOG"
if [[ "$*" == *'sudo -n'* && "${RBF_BUILD_RESTORE_OMIT_MARKER:-false}" != true ]]; then
  if [[ "$*" == *'--mode commit'* ]]; then
    printf '[build-restore] Post-commit counts: builds=27 slots=625 classifications=62\n'
    printf '[build-restore] Committed import passed all post-import checks.\n'
  else
    printf '[build-restore] Dry run passed; transaction was rolled back.\n'
  fi
fi
EOF
chmod +x "$work/bin/scp" "$work/bin/ssh"

output="$(PATH="$work/bin:$PATH" RBF_BUILD_RESTORE_TEST_LOG="$work/calls.log" \
  "$RESTORE" --config "$work/origin.env" --dry-run-only)"
[[ "$output" == *'Owner mapping: admin -> admin'* ]] || fail 'default admin mapping was not presented'
[[ "$output" == *'Dry run passed; no target data was changed.'* ]] || fail 'dry-run-only did not finish safely'
grep -q -- '--mode dry-run' "$work/calls.log" || fail 'remote dry-run mode was not selected'
grep -q -- '--owner-variable owner_admin=admin' "$work/calls.log" || fail 'admin mapping was not transferred'
grep -q -- '--owner-variable owner_puszpang=puszpang' "$work/calls.log" || fail 'puszpang mapping was not transferred'
grep -q -- '--owner-variable owner_nostrapi=nostrapi' "$work/calls.log" || fail 'nostrapi mapping was not transferred'

if PATH="$work/bin:$PATH" RBF_BUILD_RESTORE_TEST_LOG="$work/calls.log" \
  "$RESTORE" --config "$work/origin.env" --owner missing=admin --dry-run-only >/dev/null 2>&1; then
  fail 'an owner absent from the backup contract was accepted'
fi

if PATH="$work/bin:$PATH" RBF_BUILD_RESTORE_TEST_LOG="$work/missing-marker.log" \
  RBF_BUILD_RESTORE_OMIT_MARKER=true "$RESTORE" --config "$work/origin.env" \
  --dry-run-only >/dev/null 2>&1; then
  fail 'a remote run without its completion marker was accepted'
fi

production_output="$(PATH="$work/bin:$PATH" RBF_BUILD_RESTORE_TEST_LOG="$work/production.log" \
  "$RESTORE" --production --config "$work/origin.env" --dry-run-only)"
[[ "$production_output" == *'[build-restore:production]'* ]] || fail 'explicit production target was not preserved'

grep -q 'backup.lock' "$REMOTE" || fail 'commit does not serialize against scheduled backups'
grep -q 'backup-postgres.sh' "$REMOTE" || fail 'commit does not create a PostgreSQL safety dump'
if grep -q 'run-consistent-backup.sh' "$REMOTE"; then fail 'build restore still invokes the full recovery preflight'; fi
grep -q 'dry_run=1' "$REMOTE" || fail 'remote helper lost rollback-only mode'
grep -q 'dry_run=0' "$REMOTE" || fail 'remote helper lost explicit commit mode'
grep -q 'checksum mismatch' "$REMOTE" || fail 'remote helper does not verify the transferred artifact'
grep -q 'Installed migration artifact is missing' "$REMOTE" || fail 'remote helper does not verify artifact installation'
grep -q 'Post-commit counts' "$REMOTE" || fail 'remote helper does not verify committed row counts'
grep -q -- '--helper-sha256' "$RESTORE" || fail 'origin wrapper does not transfer the helper checksum'
grep -q 'tee "$remote_output_capture"' "$RESTORE" || fail 'remote progress output is not streamed live'
if grep -q 'bash -s' "$RESTORE"; then fail 'origin wrapper still streams the helper through SSH stdin'; fi
grep -q -- '--expected-builds' "$RESTORE" || fail 'origin wrapper does not transfer expected row counts'

printf '[build-restore-test] OK: artifact discovery, owner mapping, dry run and target selection\n'
