#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
python3 "$ROOT_DIR/scripts/package_deployment_artifact.py" --version "$(cat "$ROOT_DIR/VERSION")" --jar "$work/rbf-api.jar" --frontend-dist "$work/frontend" --output-dir "$work/release" --source-revision test
artifact="$(find "$work/release" -name 'rbf-deployment-*.tar.gz' -print -quit)"
python3 "$ROOT_DIR/infrastructure/scripts/release/verify-artifact.py" "$artifact" "$work/extracted" >/dev/null
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
grep -q 'run-consistent-backup.sh' "$ROOT_DIR/infrastructure/scripts/release/install-artifact.sh"
grep -q 'prepare_flyway_cutover' "$ROOT_DIR/infrastructure/scripts/lib/docker.sh"
printf '[updates] OK: compiled artifact inventory, tamper detection and operation contract\n'
