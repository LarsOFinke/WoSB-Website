#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
mkdir -p "$work/frontend" "$work/release" "$work/extracted"
printf '<!doctype html><title>RBF</title>\n' > "$work/frontend/index.html"
python3 - "$work/rbf-api.jar" <<'PY'
from pathlib import Path
import zipfile,sys
p=Path(sys.argv[1])
with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_STORED) as z:
    z.writestr('META-INF/MANIFEST.MF','Manifest-Version: 1.0\nMain-Class: org.springframework.boot.loader.launch.JarLauncher\n')
    z.writestr('BOOT-INF/classes/padding.bin',b'RBF0'*(300_000))
PY
python3 "$ROOT_DIR/infrastructure/scripts/release/package_deployment_artifact.py" --version "$(cat "$ROOT_DIR/VERSION")" --jar "$work/rbf-api.jar" --frontend-dist "$work/frontend" --output-dir "$work/release" --source-revision test
artifact="$(find "$work/release" -name 'rbf-deployment-*.tar.gz' -print -quit)"
python3 "$ROOT_DIR/infrastructure/scripts/release/verify-artifact.py" "$artifact" "$work/extracted" >/dev/null
if find "$work/extracted/payload/infrastructure/scripts" -type f \
    \( -path '*/quality/*' -o -path '*/generation/*' -o -name 'package_*.py' \) -print -quit | grep -q .; then
  echo '[updates] repository-only scripts leaked into the runtime artifact' >&2
  exit 1
fi
printf 'tamper' >> "$work/extracted/payload/artifacts/rbf-api.jar"
python3 - "$work/extracted" <<'PY'
import importlib.util,sys
from pathlib import Path
module_path=Path('infrastructure/scripts/release/verify-artifact.py').resolve()
spec=importlib.util.spec_from_file_location('verify_artifact',module_path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
manifest=__import__('json').loads((Path(sys.argv[1])/'manifest.json').read_text())
entry=next(e for e in manifest['files'] if e['path']=='payload/artifacts/rbf-api.jar')
if m.digest(Path(sys.argv[1])/entry['path']) == entry['sha256']: raise SystemExit('tamper check did not detect change')
PY
for operation in update restart rollback; do grep -q "${operation}" "$ROOT_DIR/infrastructure/scripts/services/update.sh" || exit 1; done
! grep -q 'update_migrate' "$ROOT_DIR/frontend/src/modules/admin/components/SystemOperationsPanel.vue"
! grep -q -- '--skip-backup --no-backup' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
! grep -q -- '--replace-active' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'backup_runner="$SCRIPT_DIR/../backup/run-consistent-backup.sh"' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q 'RBF_RUNTIME_INFRA_DIR="$previous_release/infrastructure"' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q 'maintenance_enable_for.*update' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q 'maintenance_disable_for succeeded' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q 'maintenance_enable_for_rollback' "$ROOT_DIR/infrastructure/scripts/release/rollback-release.sh"
grep -q 'MAINTENANCE_URL' "$ROOT_DIR/infrastructure/compose.release.yml"
grep -q 'RBF_RUNTIME_INFRA_DIR' "$ROOT_DIR/infrastructure/scripts/lib/common.sh"
grep -q 'Production environment and first-run credentials were generated on the target' "$ROOT_DIR/infrastructure/scripts/release/prepare-website-env.sh"
grep -q -- '--letsencrypt-email' "$ROOT_DIR/infrastructure/scripts/release/setup_website.sh"
grep -q 'RBF_DEPLOY_LETSENCRYPT_EMAIL' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'smoke_args+=(--bootstrap-login)' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q -- '--bootstrap-login' "$ROOT_DIR/infrastructure/scripts/checks/smoke-test.sh"
! grep -Eq 'timeout [^ ]+ systemctl restart rbf-hub\.service' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q '^TimeoutStartSec=10min$' "$ROOT_DIR/infrastructure/systemd/rbf-hub.service"
grep -q 'SEED_ADMIN_PASSWORD' "$ROOT_DIR/infrastructure/scripts/checks/smoke-test.sh"
grep -q '/api/fleets/manageable' "$ROOT_DIR/infrastructure/scripts/checks/smoke-test.sh"
grep -q '/manage' "$ROOT_DIR/infrastructure/scripts/checks/smoke-test.sh"
grep -q 'include_inactive=true' "$ROOT_DIR/infrastructure/scripts/checks/smoke-test.sh"
! grep -q '"$previous_release/infrastructure/scripts/backup/run-consistent-backup.sh"' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q 'prepare_flyway_cutover' "$ROOT_DIR/infrastructure/scripts/lib/docker.sh"
grep -q -- '--identity-file' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'RBF_DEPLOY_IDENTITY_FILE' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q -- '-o BatchMode=yes' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q -- '-o IdentitiesOnly=yes' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'discover_identity_file' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'RBF_DEPLOY_USER=rbfadmin' "$ROOT_DIR/.env.origin.test.example"
grep -q 'RBF_DEPLOY_USER=rbfadmin' "$ROOT_DIR/.env.origin.production.example"
grep -q 'target_environment="$RBF_ORIGIN_TARGET"' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q '\.env.origin.\$target_environment' "$ROOT_DIR/infrastructure/scripts/lib/origin-target.sh"
grep -q -- '--configure' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'sudo -n' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q -- '--bootstrap-user' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q -- '--bootstrap-identity-file' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'provision-ssh-admin.sh' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'bootstrap_user.*== root' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'configure_deploy_identity' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'configure_bootstrap_access' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'rbf_origin_default_identity_path' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'SSH public-key material must be supplied from outside the repository' \
  "$ROOT_DIR/infrastructure/scripts/setup/provision-ssh-admin.sh"
grep -q 'External identity for \$bootstrap_user (blank = SSH configuration/agent/password):' \
  "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh" \
  || exit 1

grep -q -- '--target-environment "$target_environment"' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh"
grep -q 'DEPLOYMENT_ENVIRONMENT' "$ROOT_DIR/infrastructure/scripts/release/setup_website.sh"
! grep -q '127.0.0.1:${POSTGRES_LOCAL_PORT:-15432}:5432' "$ROOT_DIR/infrastructure/compose.release.yml"
printf '[updates] OK: compiled artifact inventory, tamper detection and operation contract\n'
