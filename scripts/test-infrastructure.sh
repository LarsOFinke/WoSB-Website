#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infrastructure"
BACKEND_DIR="$ROOT_DIR/backend"

require_file() {
  [[ -f "$1" ]] || {
    printf 'Missing required file: %s\n' "$1" >&2
    exit 1
  }
}

require_pattern() {
  local pattern="$1"
  local file="$2"
  grep -q -- "$pattern" "$file" || {
    printf 'Expected pattern %q in %s\n' "$pattern" "$file" >&2
    exit 1
  }
}

reject_pattern() {
  local pattern="$1"
  local file="$2"
  if grep -q -- "$pattern" "$file"; then
    printf 'Unexpected pattern %q in %s\n' "$pattern" "$file" >&2
    exit 1
  fi
}

shell_files=("$ROOT_DIR/setup.sh" "$ROOT_DIR/update.sh")
while IFS= read -r file; do
  shell_files+=("$file")
done < <(
  find \
    "$INFRA_DIR" \
    "$ROOT_DIR/scripts" \
    "$BACKEND_DIR/scripts" \
    -type f -name '*.sh' -print | sort
)
for file in "${shell_files[@]}"; do
  bash -n "$file"
done

(
  source "$INFRA_DIR/scripts/lib/host/control.sh"
  claim_tmp="$(mktemp -d)"
  trap 'rm -rf "$claim_tmp"' EXIT
  printf '{"operation":"update"}\n' > "$claim_tmp/request.json"
  chmod 600 "$claim_tmp/request.json"
  claim_control_request \
    "$claim_tmp/request.json" \
    "$claim_tmp/private/request.json" \
    "$(id -u)"
  [[ ! -e "$claim_tmp/request.json" ]]
  cmp -s "$claim_tmp/private/request.json" <(printf '{"operation":"update"}\n')

  printf '{"operation":"update"}\n' > "$claim_tmp/target.json"
  chmod 600 "$claim_tmp/target.json"
  ln -s "$claim_tmp/target.json" "$claim_tmp/symlink.json"
  if claim_control_request \
    "$claim_tmp/symlink.json" \
    "$claim_tmp/private/symlink.json" \
    "$(id -u)" 2>/dev/null; then
    echo 'Control request claim must reject symbolic links.' >&2
    exit 1
  fi
)

[[ ! -e "$BACKEND_DIR/.env" ]]
[[ ! -e "$ROOT_DIR/frontend/.env" ]]
[[ ! -e "$INFRA_DIR/.env" ]]
reject_pattern '/var/run/docker.sock' "$INFRA_DIR/compose.yml"
if grep -R -q '/var/run/docker.sock' "$BACKEND_DIR"; then
  echo 'Backend must not access the Docker socket.' >&2
  exit 1
fi

# Stable public runners stay thin; behavior is owned by the corresponding modules.
require_pattern 'infrastructure/setup.sh' "$ROOT_DIR/setup.sh"
require_pattern 'infrastructure/scripts/services/update.sh' "$ROOT_DIR/update.sh"
require_pattern 'source "$INFRA_DIR/scripts/setup/main.sh"' "$INFRA_DIR/setup.sh"
require_pattern 'source "$INFRA_DIR/scripts/update/main.sh"' "$INFRA_DIR/scripts/services/update.sh"
require_file "$ROOT_DIR/scripts/package_deployment_artifact.py"
require_file "$INFRA_DIR/scripts/release/build-artifact.sh"
require_file "$INFRA_DIR/scripts/release/transfer-artifact.sh"
require_file "$INFRA_DIR/scripts/release/build-and-transfer.sh"
require_file "$INFRA_DIR/scripts/release/install-artifact.sh"
require_file "$INFRA_DIR/scripts/update/artifact.sh"
require_pattern '--artifact FILE' "$INFRA_DIR/scripts/update/options.sh"
require_pattern '--components LIST' "$INFRA_DIR/scripts/update/options.sh"
require_pattern 'update_component_enabled' "$INFRA_DIR/scripts/update/options.sh"
require_pattern 'sha256sum --check SHA256SUMS' "$INFRA_DIR/scripts/update/artifact.sh"
require_pattern 'docker load --input' "$INFRA_DIR/scripts/update/artifact.sh"
require_pattern 'Vorgebaute Deployment-Images' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'Migrationen und idempotentes Seed sind verpflichtend' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'Kein .git-Verzeichnis und kein Deployment-Artefakt' "$INFRA_DIR/scripts/update/repository.sh"
require_pattern 'Rollback-Rebuild übersprungen' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'sudo ./update.sh --seed' "$ROOT_DIR/.github/workflows/deploy.yml"
require_pattern 'Keine API-Komponente ausgewählt' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'components' "$INFRA_DIR/scripts/lib/docker.sh"
require_file "$INFRA_DIR/scripts/backup/restore-data.sh"
require_pattern '--components' "$INFRA_DIR/scripts/backup/restore-data.sh"
require_pattern 'restore_files' "$INFRA_DIR/scripts/backup/backup_runner_restore.py"
require_pattern 'z "\${ARTIFACT_FILE:-}\"' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'mktemp "\$certificate_dir/.fullchain.pem.' "$INFRA_DIR/scripts/tls/sync-certificate.sh"
require_pattern 'mv -fT "\$temporary_fullchain"' "$INFRA_DIR/scripts/tls/sync-certificate.sh"

# Update and first-run safety rules live in their focused modules.
require_pattern 'update_migrate)' "$INFRA_DIR/scripts/update/request.sh"
require_pattern 'update_migrate_seed)' "$INFRA_DIR/scripts/update/request.sh"
require_pattern 'flock -n' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'data/postgres/PG_VERSION' "$INFRA_DIR/scripts/setup/workflow.sh"
require_pattern 'scripts/lib/env.sh' "$INFRA_DIR/scripts/checks/doctor.sh"
require_pattern 'os.chown(temporary, 10001, 10001)' "$INFRA_DIR/scripts/lib/maintenance.sh"
require_pattern 'data/postgres/PG_VERSION' "$INFRA_DIR/scripts/lib/host/storage.sh"
require_pattern 'AUTO_SEED=true rbf-seed' "$INFRA_DIR/compose.yml"
require_pattern '^AUTO_SEED=false$' "$INFRA_DIR/.env.example"
require_file "$ROOT_DIR/spring-api/Dockerfile"
require_file "$ROOT_DIR/spring-api/pom.xml"
require_pattern 'proxy_pass http://secure-api:8080' "$INFRA_DIR/nginx/default.conf"
require_pattern 'anyRequest().denyAll()' "$ROOT_DIR/spring-api/src/main/java/eu/royalblackwater/api/config/SecurityConfiguration.java"

# The backend intentionally requires an env file. The image contains an empty,
# assignment-free marker while Compose injects real values as process variables.
require_file "$BACKEND_DIR/config/container.env"
require_pattern '^COPY config ./config$' "$BACKEND_DIR/Dockerfile"
require_pattern 'RBF_ALEMBIC_CONFIG=/app/alembic.ini' "$BACKEND_DIR/Dockerfile"
python3 - "$BACKEND_DIR/config/container.env" "$INFRA_DIR/compose.yml" <<'PY_CONFIG'
from pathlib import Path
import sys

container_env = Path(sys.argv[1])
compose_file = Path(sys.argv[2])
assignments = [
    line.strip()
    for line in container_env.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]
assert not assignments, "backend/config/container.env must not contain runtime assignments"

compose = compose_file.read_text(encoding="utf-8")
for service, next_service in (("migrate", "seed"), ("seed", "api"), ("api", "gateway")):
    section = compose.split(f"  {service}:\n", 1)[1].split(f"\n  {next_service}:\n", 1)[0]
    assert "    env_file:\n      - .env\n" in section, f"{service} must receive infrastructure/.env"
    assert "      RBF_ENV_FILE: /app/config/container.env\n" in section, (
        f"{service} must point the backend loader at the image marker file"
    )
PY_CONFIG

python3 - \
  "$BACKEND_DIR/config/application.cfg" \
  "$ROOT_DIR/frontend/.env.example" \
  "$INFRA_DIR/compose.yml" \
  "$INFRA_DIR/nginx/default.conf" <<'PY_API_PREFIX'
from configparser import ConfigParser
from pathlib import Path
import sys

application_cfg = Path(sys.argv[1])
frontend_env = Path(sys.argv[2])
compose_file = Path(sys.argv[3])
nginx_file = Path(sys.argv[4])

parser = ConfigParser(interpolation=None)
assert parser.read(application_cfg, encoding="utf-8") == [str(application_cfg)]
api_prefix = parser.get("app", "api_prefix").strip().rstrip("/")
assert api_prefix.startswith("/"), "Backend API prefix must be absolute"

frontend_values = {}
for raw_line in frontend_env.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    frontend_values[key.strip()] = value.strip()
assert frontend_values.get("VITE_API_BASE_URL", "").rstrip("/") == api_prefix, (
    "Frontend API base must match backend [app].api_prefix"
)

compose = compose_file.read_text(encoding="utf-8")
assert f"VITE_API_BASE_URL: {api_prefix}" in compose, "Compose frontend build arg must match API prefix"
nginx = nginx_file.read_text(encoding="utf-8")
assert f"location {api_prefix}/" in nginx, "NGINX must proxy the configured API prefix"
PY_API_PREFIX

python3 - "$INFRA_DIR/compose.yml" <<'PY_COMPOSE'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
api_section = text.split("  api:\n", 1)[1].split("\n  gateway:\n", 1)[0]
networks_section = text.split("\nnetworks:\n", 1)[1]
assert "      - backend\n      - outbound\n" in api_section, (
    "API must retain database isolation and outbound egress"
)
assert "  backend:\n    driver: bridge\n    internal: true\n" in networks_section, (
    "backend network must remain internal"
)
assert "  outbound:\n    driver: bridge\n" in networks_section, "outbound network must be defined"
secure_api_section = text.split("  secure-api:\n", 1)[1].split("\n  gateway:\n", 1)[0]
assert "      - backend\n" in secure_api_section, "secure-api must stay on the internal backend network"
assert "      - outbound\n" not in secure_api_section, "secure-api must not receive general outbound egress"
assert "    read_only: true\n" in secure_api_section, "secure-api root filesystem must be read-only"
assert "      - ALL\n" in secure_api_section, "secure-api must drop Linux capabilities"
PY_COMPOSE

if docker compose version >/dev/null 2>&1; then
  cp "$INFRA_DIR/.env.example" "$INFRA_DIR/.env"
  trap 'rm -f "$INFRA_DIR/.env"' EXIT
  (cd "$INFRA_DIR" && docker compose -f compose.yml config >/dev/null)
fi

require_pattern 'limit_req_zone.*auth_login' "$INFRA_DIR/nginx/default.conf"
require_pattern 'Strict-Transport-Security' "$INFRA_DIR/nginx/security-headers.conf"
require_pattern '--no-proxy-headers' "$BACKEND_DIR/Dockerfile"
require_file "$INFRA_DIR/nginx/security-headers.conf"
require_file "$INFRA_DIR/nginx/upload-security-headers.conf"
require_pattern 'Content-Security-Policy' "$INFRA_DIR/nginx/security-headers.conf"
require_pattern 'Content-Security-Policy.*sandbox' "$INFRA_DIR/nginx/upload-security-headers.conf"
require_pattern 'rbf-security-headers.conf' "$INFRA_DIR/nginx/default.conf"
require_pattern 'rbf-upload-security-headers.conf' "$INFRA_DIR/nginx/default.conf"
python3 - "$INFRA_DIR/nginx/default.conf" <<'PY_UPLOAD_PROXY'
from pathlib import Path
import sys

nginx = Path(sys.argv[1]).read_text(encoding="utf-8")
upload_block = nginx.split("    location /uploads/ {", 1)[1].split("\n    }", 1)[0]
assert "proxy_pass http://api:8000;" in upload_block, "legacy upload access policy must be enforced by the API"
assert 'Cache-Control "private, no-store" always' in upload_block, "uploads must not use a public cache"
assert "immutable" not in upload_block and "max-age" not in upload_block, "uploads must not be publicly cacheable"
PY_UPLOAD_PROXY
reject_pattern '\$proxy_add_x_forwarded_for' "$INFRA_DIR/nginx/default.conf"
require_pattern 'X-Forwarded-For \$remote_addr' "$INFRA_DIR/nginx/default.conf"
require_pattern 'data/control/inbox:/run/rbf-control/inbox' "$INFRA_DIR/compose.yml"
require_pattern 'data/control/status:/run/rbf-control/status:ro' "$INFRA_DIR/compose.yml"
require_pattern 'claim_control_request' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'restart-application.sh' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'bw_compose restart api' "$INFRA_DIR/scripts/services/restart-application.sh"
require_pattern 'wait_for_api' "$INFRA_DIR/scripts/services/restart-application.sh"
require_pattern 'API-Readiness blieb aus' "$INFRA_DIR/scripts/lib/docker.sh"
require_pattern 'bw_compose logs --tail=.*api' "$INFRA_DIR/scripts/lib/docker.sh"
reject_pattern 'bw_compose restart gateway' "$INFRA_DIR/scripts/services/restart-application.sh"
require_pattern 'maintenance_enable restart' "$INFRA_DIR/scripts/services/restart-application.sh"
require_pattern 'maintenance_enable update' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'maintenance_enable restore' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern 'maintenance_disable' "$INFRA_DIR/scripts/services/restart-application.sh"
require_file "$INFRA_DIR/scripts/lib/maintenance.sh"
require_pattern 'PY_MAINTENANCE_FALLBACK' "$INFRA_DIR/scripts/lib/maintenance.sh"
require_file "$ROOT_DIR/frontend/public/maintenance.html"
require_pattern 'maintenance-mode.json' "$INFRA_DIR/nginx/default.conf"
require_pattern 'error_page 503 /maintenance.html' "$INFRA_DIR/nginx/default.conf"
require_pattern 'Retry-After "120"' "$INFRA_DIR/nginx/default.conf"
reject_pattern 'restart postgres' "$INFRA_DIR/scripts/services/restart-application.sh"
require_pattern 'member.isdir() or member.isfile()' "$INFRA_DIR/scripts/backup/restore-data.sh"
require_pattern 'find /usr/share/nginx/html -type d -exec chmod 0755' "$INFRA_DIR/docker/frontend.Dockerfile"
require_pattern 'find /usr/share/nginx/html -type f -exec chmod 0644' "$INFRA_DIR/docker/frontend.Dockerfile"
reject_pattern 'host.docker.internal' "$INFRA_DIR/compose.yml"
reject_pattern '/integrations/discord/webhooks/rbf' "$INFRA_DIR/nginx/default.conf"
require_pattern 'read_database_schema_state' "$INFRA_DIR/scripts/update/workflow.sh"
reject_pattern 'migration_files_changed' "$INFRA_DIR/scripts/update/repository.sh"
require_pattern 'update_capture_running_images' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'heartbeat_at' "$INFRA_DIR/scripts/update/status.sh"
require_pattern 'update_run_backup_scripts true' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'run-consistent-backup.sh' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern '--lock-held' "$INFRA_DIR/scripts/update/workflow.sh"
reject_pattern 'backup/backup-all.sh' "$INFRA_DIR/scripts/update/workflow.sh"
require_pattern 'bw_compose stop api' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
reject_pattern 'bw_compose stop api gateway' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern 'run-consistent-backup.sh' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern '--preflight-only' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern 'CREATE DATABASE %I OWNER %I TEMPLATE template0' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern 'python -m app.db.restore_preflight' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern 'application_readiness_preflight' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern 'rollback_database_swap' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
reject_pattern '-c "SELECT pg_terminate_backend' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_file "$INFRA_DIR/scripts/backup/backup_metadata.py"
require_file "$INFRA_DIR/scripts/backup/backup_set_manifest.py"
require_file "$INFRA_DIR/scripts/backup/recovery_report.py"
require_file "$INFRA_DIR/scripts/backup/recovery_preflight.py"
require_file "$INFRA_DIR/scripts/backup/run-consistent-backup.sh"
require_file "$INFRA_DIR/scripts/backup/merge-encryption-keyring.sh"
require_pattern 'backup_metadata.py' "$INFRA_DIR/scripts/backup/backup-postgres.sh"
require_pattern "-mindepth 2" "$INFRA_DIR/scripts/checks/doctor.sh"
require_pattern 'start_new_session=True' "$ROOT_DIR/scripts/run_backend_tests.py"
require_pattern 'timeout=timeout_seconds' "$ROOT_DIR/scripts/run_backend_tests.py"

python3 - "$INFRA_DIR/scripts/update/workflow.sh" <<'PY_UPDATE_ORDER'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding='utf-8')
run = text.split('update_run() {', 1)[1]
assert run.index('update_acquire_lock') < run.index('update_claim_admin_request'), (
    'update lock must be acquired before claiming an admin request'
)
PY_UPDATE_ORDER

bash "$ROOT_DIR/scripts/test-update-management.sh"

require_file "$INFRA_DIR/systemd/rbf-hub-backup-admin.path"
require_file "$INFRA_DIR/systemd/rbf-hub-backup-admin.service"
require_pattern 'backup.request' "$INFRA_DIR/systemd/rbf-hub-backup-admin.path"
require_pattern 'backup-from-admin.sh' "$INFRA_DIR/systemd/rbf-hub-backup-admin.service"
require_pattern 'rbf-hub-backup-admin.path' "$INFRA_DIR/scripts/deployment/install-systemd.sh"
require_pattern 'control/secrets' "$INFRA_DIR/scripts/lib/host/storage.sh"
require_pattern 'BACKUP_RESULT_FILE' "$INFRA_DIR/scripts/backup/backup-postgres.sh"
require_pattern 'BACKUP_RESULT_FILE' "$INFRA_DIR/scripts/backup/backup-data.sh"
require_pattern 'data/uploads' "$INFRA_DIR/scripts/backup/backup-data.sh"
require_pattern 'letsencrypt' "$INFRA_DIR/scripts/backup/backup-data.sh"
require_file "$INFRA_DIR/scripts/backup/backup-recovery.sh"
require_file "$INFRA_DIR/scripts/backup/restore-recovery.sh"
require_file "$INFRA_DIR/scripts/backup/verify-recovery.sh"
require_file "$INFRA_DIR/scripts/backup/recovery_bundle.py"
require_file "$ROOT_DIR/tools/windows/New-RbfRecoveryKey.ps1"
require_file "$ROOT_DIR/tools/windows/Pull-RbfRecovery.ps1"
require_file "$ROOT_DIR/tools/windows/Test-RbfRecovery.ps1"
require_file "$ROOT_DIR/docs/deployment/DISASTER_RECOVERY.md"
require_pattern 'BACKUP_RECOVERY_ENABLED=false' "$INFRA_DIR/.env.example"
require_pattern 'BACKUP_AGE_RECIPIENT=' "$INFRA_DIR/.env.example"
require_pattern 'BACKUP_PULL_EXPORT_DIR=' "$INFRA_DIR/.env.example"
require_pattern 'age ca-certificates' "$INFRA_DIR/scripts/lib/host/packages.sh"
require_pattern 'unattended-upgrades' "$INFRA_DIR/scripts/lib/host/packages.sh"
require_pattern 'apt-daily-upgrade.timer' "$INFRA_DIR/scripts/lib/host/packages.sh"
reject_pattern 'usermod -aG docker' "$INFRA_DIR/scripts/lib/host/packages.sh"
require_pattern 'ufw default deny incoming' "$INFRA_DIR/scripts/lib/host/firewall.sh"
require_file "$INFRA_DIR/scripts/checks/host-security.sh"
require_pattern 'run-consistent-backup.sh' "$INFRA_DIR/scripts/backup/backup-all.sh"
require_pattern 'infrastructure.env' "$INFRA_DIR/scripts/backup/backup-recovery.sh"
require_pattern 'backend-config' "$INFRA_DIR/scripts/backup/backup-recovery.sh"
require_pattern 'control-secrets' "$INFRA_DIR/scripts/backup/backup-recovery.sh"
require_pattern 'secret-keyring.json' "$INFRA_DIR/scripts/backup/backup-recovery.sh"
require_pattern 'restore-postgres.sh' "$INFRA_DIR/scripts/backup/restore-recovery.sh"
require_pattern 'restore-data.sh' "$INFRA_DIR/scripts/backup/restore-recovery.sh"
require_pattern 'setup.sh.*--profile.*--no-start' "$INFRA_DIR/scripts/backup/restore-recovery.sh"
require_pattern 'StrictHostKeyChecking=yes' "$INFRA_DIR/scripts/backup/backup_runner_transfer.py"
require_pattern 'sftp-roundtrip' "$INFRA_DIR/scripts/backup/backup_runner_transfer.py"
reject_pattern 'sha256sum -c' "$INFRA_DIR/scripts/backup/backup_runner_transfer.py"
require_file "$INFRA_DIR/scripts/backup/local_backup_catalog.py"
require_file "$INFRA_DIR/scripts/backup/arm-admin-restore.sh"
require_pattern 'O_NOFOLLOW' "$INFRA_DIR/scripts/backup/local_backup_catalog.py"
require_pattern 'token_sha256' "$INFRA_DIR/scripts/backup/arm-admin-restore.sh"
require_pattern 'RBF_RESTORE_LOCK_HELD' "$INFRA_DIR/scripts/backup/restore-postgres.sh"
require_pattern 'exec 8>"$run_dir/update.lock"' "$INFRA_DIR/scripts/services/backup-from-admin.sh"
require_pattern 'exec 9>"$run_dir/backup.lock"' "$INFRA_DIR/scripts/services/backup-from-admin.sh"
require_pattern '--all-locks-held' "$INFRA_DIR/scripts/backup/backup_runner_transfer.py"
require_pattern 'exec 9>"$run_dir/update.lock"' "$INFRA_DIR/scripts/backup/run-consistent-backup.sh"
require_pattern 'exec 8>"$run_dir/backup.lock"' "$INFRA_DIR/scripts/backup/run-consistent-backup.sh"
require_pattern 'backup_set_manifest.py' "$INFRA_DIR/scripts/backup/run-consistent-backup.sh"
require_pattern 'export_verified_recovery_set' "$INFRA_DIR/scripts/backup/run-consistent-backup.sh"
require_pattern 'copy_atomic "$set_manifest"' "$INFRA_DIR/scripts/backup/run-consistent-backup.sh"
reject_pattern 'BACKUP_PULL_EXPORT_DIR' "$INFRA_DIR/scripts/backup/backup-recovery.sh"
require_pattern 'python -m uvicorn main:app --app-dir src' "$INFRA_DIR/scripts/backup/restore-postgres.sh"

python3 - \
  "$INFRA_DIR/scripts/services/backup-from-admin.sh" \
  "$INFRA_DIR/scripts/backup/run-consistent-backup.sh" \
  "$INFRA_DIR/scripts/backup/backup_runner_transfer.py" <<'PY_BACKUP_LOCKS'
from pathlib import Path
import sys

admin_service = Path(sys.argv[1]).read_text(encoding="utf-8")
coordinator = Path(sys.argv[2]).read_text(encoding="utf-8")
admin_runner = Path(sys.argv[3]).read_text(encoding="utf-8")
assert admin_service.index('exec 8>"$run_dir/update.lock"') < admin_service.index('flock 8')
assert admin_service.index('flock 8') < admin_service.index('exec 9>"$run_dir/backup.lock"')
assert admin_service.index('flock 9') < admin_service.index('claim_control_request')
assert coordinator.index('exec 9>"$run_dir/update.lock"') < coordinator.index('flock 9')
assert coordinator.index('flock 9') < coordinator.index('exec 8>"$run_dir/backup.lock"')
assert coordinator.index('flock 8') < coordinator.index('backup-postgres.sh')
assert 'if [[ "$lock_held" != true' in coordinator
assert 'if [[ "$all_locks_held" != true' in coordinator
assert '"--all-locks-held"' in admin_runner
PY_BACKUP_LOCKS


python3 - "$INFRA_DIR/scripts/backup/recovery_bundle.py" <<'PY_RECOVERY_BUNDLE'
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import sys

script = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("rbf_recovery_bundle", script)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    stage = root / "stage"
    for directory in (
        stage / "artifacts/postgres",
        stage / "artifacts/files",
        stage / "configuration/backend-config",
        stage / "system",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    (stage / "artifacts/postgres/db.sql.gz").write_bytes(b"database")
    (stage / "artifacts/files/files.tar.gz").write_bytes(b"files")
    (stage / "configuration/infrastructure.env").write_text("SECRET=value\n", encoding="utf-8")
    (stage / "configuration/backend-config/application.cfg").write_text("[app]\n", encoding="utf-8")
    (stage / "system/backup-metadata.json").write_text(
        json.dumps({"version": "1.0.0", "git_commit": "test"}), encoding="utf-8"
    )
    module.build_manifest(stage, "db.sql.gz", "files.tar.gz")
    archive = root / "bundle.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        for name in ("manifest.json", "artifacts", "configuration", "system"):
            handle.add(stage / name, arcname=name)
    extracted = root / "extracted"
    module.extract_safely(archive, extracted)
    manifest = module.verify_extracted(extracted)
    assert manifest["artifacts"]["postgres"] == "artifacts/postgres/db.sql.gz"
    assert len(manifest["files"]) == 5

    (extracted / "configuration/infrastructure.env").write_text("tampered", encoding="utf-8")
    try:
        module.verify_extracted(extracted)
    except RuntimeError as exc:
        assert "checksum mismatch" in str(exc) or "size mismatch" in str(exc)
    else:
        raise AssertionError("Tampered recovery content must fail verification")

    unsafe = root / "unsafe.tar.gz"
    with tarfile.open(unsafe, "w:gz") as handle:
        info = tarfile.TarInfo("../escape")
        info.size = 0
        import io
        handle.addfile(info, io.BytesIO(b""))
    try:
        module.extract_safely(unsafe, root / "unsafe-output")
    except RuntimeError as exc:
        assert "Unsafe path" in str(exc)
    else:
        raise AssertionError("Path traversal must be rejected")
PY_RECOVERY_BUNDLE

python3 - "$INFRA_DIR/scripts/backup/backup-admin-runner.py" <<'PY_BACKUP_RUNNER'
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

script = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("rbf_backup_admin_runner", script)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as temporary:
    infra = Path(temporary) / "infrastructure"
    request = infra / "data/control/run/request.json"
    request.parent.mkdir(parents=True)
    runner = module.Runner(infra, request)
    runner.prepare()

    def fake_fingerprint(_line):
        return "SHA256:test-host-key"

    def fake_private_key(content):
        temporary_key = runner.run_dir / "validated-private-key"
        temporary_key.write_text(content, encoding="utf-8")
        os.chmod(temporary_key, 0o600)
        return temporary_key

    runner.fingerprint_for_line = fake_fingerprint
    runner.validate_private_key = fake_private_key
    runner.test_connection = lambda *_args, **_kwargs: "2026-08-01T12:00:00+00:00"
    runner.request = {
        "operation": "configure",
        "host": "backup.example.net",
        "port": 2222,
        "username": "rbf_backup",
        "remote_directory": "/srv/backups/rbf",
        "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestHostKeyMaterial",
        "private_key": "test-private-key\n",
    }
    runner.configure()
    config = json.loads(runner.config_file.read_text(encoding="utf-8"))
    assert config["host"] == "backup.example.net"
    assert config["remote_directory"] == "/srv/backups/rbf"
    assert "private_key" not in config
    assert os.stat(runner.key_file).st_mode & 0o077 == 0
    assert os.stat(runner.known_hosts_file).st_mode & 0o077 == 0
    assert runner.known_hosts_file.read_text(encoding="utf-8").startswith("[backup.example.net]:2222 ")
    assert runner.known_hosts_token("backup.example.net", 22) == "backup.example.net"
    assert runner.known_hosts_token("backup.example.net", 2222) == "[backup.example.net]:2222"

    backup_file = infra / "data/backups/postgres/rbf-test.sql.gz"
    backup_file.parent.mkdir(parents=True)
    backup_file.write_bytes(b"database-backup")
    checksum_file = Path(str(backup_file) + ".sha256")
    checksum_file.write_text(
        f"{module.hashlib.sha256(backup_file.read_bytes()).hexdigest()}  {backup_file.name}\n",
        encoding="utf-8",
    )
    calls = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    remote_payloads = {
        backup_file.name: backup_file.read_bytes(),
        checksum_file.name: checksum_file.read_bytes(),
    }

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        batch = str(kwargs.get("input") or "")
        for line in batch.splitlines():
            if line.startswith("get "):
                _, remote_name, destination = line.split(maxsplit=2)
                Path(destination).write_bytes(remote_payloads[remote_name])
        return Result()

    original_run = module.subprocess.run
    module.subprocess.run = fake_run
    try:
        transfer = runner.transfer(config, backup_file, "postgresql")
    finally:
        module.subprocess.run = original_run

    assert transfer["artifact_type"] == "postgresql"
    assert transfer["filename"] == backup_file.name
    assert transfer["size_bytes"] == len(b"database-backup")
    assert transfer["remote_path"] == f"/srv/backups/rbf/{backup_file.name}"
    assert len(calls) == 3
    assert all(call[0][0] == "sftp" for call in calls)
    assert "StrictHostKeyChecking=yes" in calls[0][0]
    assert f"put {backup_file} {backup_file.name}.part" in calls[0][1]["input"]
    assert f"get {backup_file.name}" in calls[1][1]["input"]
    assert f"get {checksum_file.name}" in calls[2][1]["input"]
PY_BACKUP_RUNNER


python3 - "$INFRA_DIR/scripts/backup/local_backup_catalog.py" <<'PY_LOCAL_CATALOG'
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile

script = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("rbf_local_backup_catalog", script)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as temporary:
    infra = Path(temporary) / "infrastructure"
    root = infra / "data/backups/postgres"
    root.mkdir(parents=True)
    backup = root / "rbf-20260731T120000Z.sql.gz"
    backup.write_bytes(b"database")
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    Path(f"{backup}.sha256").write_text(f"{digest}  {backup.name}\n", encoding="ascii")
    records, skipped = module.scan_local_postgres_backups(infra)
    assert skipped == 0 and len(records) == 1
    assert records[0].path == backup

    token = "host_approval_token_1234567890"
    approval = infra / "data/control/secrets/database-restore-approval.json"
    approval.parent.mkdir(parents=True)
    approval.write_text(json.dumps({
        "purpose": "database_restore",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
    }), encoding="utf-8")
    os.chmod(approval, 0o600)
    module.consume_database_restore_approval(infra, hashlib.sha256(token.encode()).hexdigest())
    assert not approval.exists()
PY_LOCAL_CATALOG

# Assisted backup-server enrollment must preserve upload/recovery key separation.
require_file "$ROOT_DIR/contracts/backup_enrollment.py"
require_file "$ROOT_DIR/tools/linux/recovery-tool/Provision-RbfBackupServer.sh"
require_file "$INFRA_DIR/scripts/backup/sync-backup-set-remote.py"
require_pattern 'ForceCommand internal-sftp -u 0027 -d /data' "$ROOT_DIR/tools/linux/recovery-tool/Provision-RbfBackupServer.sh"
require_pattern 'ForceCommand internal-sftp -R -d /data' "$ROOT_DIR/tools/linux/recovery-tool/Provision-RbfBackupServer.sh"
require_pattern 'from="127.0.0.1,::1"' "$ROOT_DIR/tools/linux/recovery-tool/Provision-RbfBackupServer.sh"
require_pattern 'Abbruch zum Schutz des bestehenden Kontos' "$ROOT_DIR/tools/linux/recovery-tool/Provision-RbfBackupServer.sh"
require_pattern 'Die neue SSHD-Konfiguration ist ungültig und wurde zurückgerollt' "$ROOT_DIR/tools/linux/recovery-tool/Provision-RbfBackupServer.sh"
require_pattern 'validate_manifest(infra, args.backup_set.resolve())' "$INFRA_DIR/scripts/backup/sync-backup-set-remote.py"
require_pattern 'runner.transfer(config, args.backup_set.resolve(), "backup_set")' "$INFRA_DIR/scripts/backup/sync-backup-set-remote.py"
require_pattern 'artifact_type == "backup_set"' "$INFRA_DIR/scripts/backup/backup_runner_transfer.py"

echo 'Infrastructure checks OK.'
