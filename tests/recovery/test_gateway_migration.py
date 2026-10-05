"""Exercise release handover with isolated filesystem and simulated host commands.

Only the root guard and /etc/nginx path are relocated in the sandbox copy. No
host services, containers, certificates or production files are touched.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "infrastructure/scripts/release"


def executable(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\nset -Eeuo pipefail\n" + text)
    path.chmod(0o755)


@pytest.fixture
def host(tmp_path):
    root = tmp_path / "installation"
    scripts = tmp_path / "incoming/infrastructure/scripts"
    shutil.copytree(ROOT / "infrastructure/scripts", scripts)
    nginx = tmp_path / "nginx"
    for path in scripts.rglob("*.sh"):
        path.write_text(path.read_text().replace('"$EUID"', '"0"').replace("/etc/nginx", str(nginx)))
    old = root / "releases/1.0.0/infrastructure"
    old.mkdir(parents=True)
    (old / "compose.release.yml").write_text("services: {}\n")
    (root / "current").symlink_to(old.parent)
    shared = root / "shared"
    shared.mkdir()
    (shared / ".env").write_text("DEPLOYMENT_ENVIRONMENT=test\n")
    (old / ".env").symlink_to(shared / ".env")
    shutil.copytree(ROOT / "infrastructure/scripts/lib", old / "scripts/lib")
    commands = tmp_path / "bin"
    commands.mkdir()
    log = tmp_path / "events"
    env = dict(os.environ, PATH=f"{commands}:{os.environ['PATH']}", EVENTS=str(log),
               NGINX_ROOT=str(nginx), RBF_INSTALL_ROOT=str(root))
    executable(commands / "docker", 'echo "docker $*" >> "$EVENTS"\n[[ "${FAIL_PHASE:-}" != build || " $* " != *" build "* ]]\n')
    executable(commands / "nginx", 'echo "nginx $*" >> "$EVENTS"\n')
    executable(commands / "journalctl", ':\n')
    executable(commands / "systemctl", 'echo "systemctl $*" >> "$EVENTS"\n[[ "${FAIL_PHASE:-}" != stack || "$*" != "restart rbf-hub.service" ]]\n')
    executable(commands / "vps-gateway-site-import", ':\n')
    executable(commands / "vps-gateway-init", """
echo initialize >> "$EVENTS"
[[ "${FAIL_PHASE:-}" != init ]] || exit 17
mkdir -p "$NGINX_ROOT"/{conf.d,snippets,sites-enabled,sites-available}
touch "$NGINX_ROOT/conf.d/vps-gateway.conf" "$NGINX_ROOT/snippets/vps-gateway-proxy-headers.conf"
touch "$NGINX_ROOT/sites-available/vps-gateway-catch-all.conf"
ln -s ../sites-available/vps-gateway-catch-all.conf "$NGINX_ROOT/sites-enabled/vps-gateway-catch-all.conf"
""")
    executable(scripts / "backup/run-consistent-backup.sh", """
echo backup >> "$EVENTS"
while (($#)); do
  case "$1" in
    --postgres-result|--files-result)
      result="$2"; backup="$RBF_INSTALL_ROOT/shared/$(basename "$result").backup"
      printf backup > "$backup"; sha256sum "$backup" > "$backup.sha256"
      printf '%s' "$backup" > "$result"; shift 2 ;;
    --backup-set-result) printf set > "$2"; shift 2 ;;
    *) shift ;;
  esac
done
""")
    payload = tmp_path / "payload"
    shutil.copytree(scripts.parent, payload / "infrastructure")
    infra = payload / "infrastructure"
    (payload / "VERSION").write_text("1.0.1\n")
    (infra / "nginx").mkdir()
    (infra / "nginx/host-site.conf").write_text("host template")
    (infra / "compose.release.yml").write_text("services: {}\n")
    executable(infra / "scripts/lib/env.sh", 'validate_env() { :; }\nread_env() { printf 18080; }\n')
    executable(infra / "scripts/lib/host/storage.sh", 'prepare_data_directories() { :; }\n')
    executable(infra / "scripts/deployment/install-systemd.sh", 'echo units >> "$EVENTS"\n')
    executable(infra / "scripts/lib/host/nginx.sh", """
configure_host_nginx() {
  echo site >> "$EVENTS"
  [[ "${FAIL_PHASE:-}" != site ]]
}
""")
    executable(infra / "scripts/checks/smoke-test.sh", 'echo smoke >> "$EVENTS"\n[[ "${FAIL_PHASE:-}" != smoke ]]\n')
    manifest = {"version": "1.0.1", "files": [
        {"path": "payload/" + str(path.relative_to(payload)),
         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(payload.rglob("*")) if path.is_file()
    ]}
    source_manifest = tmp_path / "manifest.json"
    source_manifest.write_text(json.dumps(manifest))
    verifier = tmp_path / "verifier.py"
    verifier.write_text("""import json, os, shutil, sys
from pathlib import Path
source = Path(os.environ['FIXTURE_PAYLOAD'])
dest = Path(sys.argv[2]); dest.mkdir(parents=True)
shutil.copytree(source, dest / 'payload')
shutil.copy(source.parent / 'manifest.json', dest / 'manifest.json')
(dest / 'SHA256SUMS').write_text('fixture inventory')
print((dest / 'manifest.json').read_text())
""")
    artifact = tmp_path / "release.tar.gz"
    artifact.write_bytes(b"immutable artifact")
    Path(str(artifact) + ".sha256").write_text(hashlib.sha256(artifact.read_bytes()).hexdigest() + "  release.tar.gz\n")
    env.update(RBF_ARTIFACT_VERIFIER=str(verifier), FIXTURE_PAYLOAD=str(payload))
    return root, scripts, artifact, source_manifest, env, log


def install(host, **extra):
    root, scripts, artifact, _, env, _ = host
    return subprocess.run(["bash", str(scripts / "release/install-artifact.sh"),
                           "--artifact", str(artifact), "--install-root", str(root)],
                          env=env | extra, text=True, capture_output=True, timeout=30)


def record(host):
    return json.loads((host[0] / "shared/deployments/1.0.1.json").read_text())


def test_handover_runs_after_backup_and_private_stack(host):
    result = install(host)
    assert result.returncode == 0, result.stdout + result.stderr
    events = host[5].read_text().splitlines()
    assert events.index("backup") < next(i for i, line in enumerate(events) if "build api gateway" in line)
    assert events.index("systemctl restart rbf-hub.service") < events.index("initialize") < events.index("site") < events.index("smoke")
    assert record(host)["state"] == "active"
    assert record(host)["host_nginx_migration"] is True
    assert (host[0] / "releases/1.0.0").is_dir()


@pytest.mark.parametrize("phase", ["stack", "init", "site", "smoke"])
def test_failed_handover_resumes_without_replacing_original_backup(host, phase):
    result = install(host, FAIL_PHASE=phase)
    assert result.returncode != 0
    before = record(host)
    assert before["state"] == "failed"
    assert (host[0] / "current").resolve().name == "1.0.1"
    result = install(host)
    assert result.returncode == 0, result.stdout + result.stderr
    after = record(host)
    assert after["state"] == "active"
    for key in ("previous_release", "previous_environment", "rollback_postgres", "rollback_files", "created_at"):
        assert after[key] == before[key]
    assert host[5].read_text().splitlines().count("backup") == 1
    assert install(host).returncode != 0  # Successful releases remain immutable.


def test_retry_rejects_changed_archive_and_payload(host):
    assert install(host, FAIL_PHASE="site").returncode != 0
    artifact = host[2]
    original = artifact.read_bytes()
    artifact.write_bytes(b"changed artifact")
    Path(str(artifact) + ".sha256").write_text(hashlib.sha256(artifact.read_bytes()).hexdigest() + "  release.tar.gz\n")
    result = install(host)
    assert result.returncode != 0 and "exact original artifact" in result.stderr
    artifact.write_bytes(original)
    Path(str(artifact) + ".sha256").write_text(hashlib.sha256(original).hexdigest() + "  release.tar.gz\n")
    (host[0] / "current/VERSION").write_text("tampered")
    result = install(host)
    assert result.returncode != 0 and "payload changed" in result.stderr


def test_partial_core_fails_before_backup_or_service_changes(host):
    nginx = Path(host[4]["NGINX_ROOT"])
    (nginx / "conf.d").mkdir(parents=True)
    (nginx / "conf.d/custom.conf").write_text("custom config")
    result = install(host)
    assert result.returncode != 0 and "Partial or custom" in result.stderr
    assert "backup" not in host[5].read_text()
    assert "systemctl" not in host[5].read_text()
    assert (host[0] / "current").resolve().name == "1.0.0"


def test_manual_rollback_refuses_legacy_before_stopping_stack(host):
    assert install(host).returncode == 0
    host[5].write_text("")
    result = subprocess.run(["bash", str(host[1] / "release/rollback-release.sh")],
                            env=host[4], text=True, capture_output=True, timeout=10)
    assert result.returncode != 0 and "Rollback across the host-NGINX migration is unsafe" in result.stderr
    assert host[5].read_text() == ""
    assert (host[0] / "current").resolve().name == "1.0.1"


def test_stack_reconciles_gateway_with_orphan_cleanup(tmp_path):
    log = tmp_path / "calls"
    script = r'''source "$1"
bw_compose() { echo "$*" >> "$CALLS"; }
ensure_postgres_service() { :; }
prepare_flyway_cutover() { :; }
run_schema_migrations() { :; }
wait_for_api() { :; }
deploy_stack
'''
    subprocess.run(["bash", "-c", script, "_", str(ROOT / "infrastructure/scripts/lib/docker.sh")],
                   env=dict(os.environ, CALLS=str(log)), check=True, capture_output=True)
    assert log.read_text().splitlines() == ["up -d --no-deps api", "up -d --no-deps --remove-orphans gateway"]


def test_interrupted_activation_can_resume(host):
    assert install(host, FAIL_PHASE="init").returncode != 0
    path = host[0] / "shared/deployments/1.0.1.json"
    metadata = json.loads(path.read_text())
    metadata["state"] = "activating"
    path.write_text(json.dumps(metadata))
    result = install(host)
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_backup_blocks_resume(host):
    assert install(host, FAIL_PHASE="site").returncode != 0
    Path(record(host)["rollback_postgres"]).unlink()
    host[5].write_text("")
    result = install(host)
    assert result.returncode != 0 and "backup is unavailable" in result.stderr
    assert "systemctl" not in host[5].read_text()


def test_image_build_failure_keeps_legacy_release_selected(host):
    result = install(host, FAIL_PHASE="build")
    assert result.returncode != 0
    assert (host[0] / "current").resolve().name == "1.0.0"
    assert "systemctl" not in host[5].read_text()
    assert "initialize" not in host[5].read_text().splitlines()


def test_migration_cannot_skip_backup(host):
    root, scripts, artifact, _, env, log = host
    result = subprocess.run(["bash", str(scripts / "release/install-artifact.sh"),
                             "--artifact", str(artifact), "--install-root", str(root), "--skip-backup"],
                            env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode != 0 and "requires the coordinated" in result.stderr
    assert "systemctl" not in log.read_text()


def test_initialized_gateway_is_preserved_on_migration(host):
    subprocess.run(["vps-gateway-init", "--empty"], env=host[4], check=True)
    host[5].write_text("")
    custom = Path(host[4]["NGINX_ROOT"]) / "sites-available/custom.conf"
    custom.write_text("preserve this unrelated site")
    result = install(host)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "initialize" not in host[5].read_text().splitlines()
    assert custom.read_text() == "preserve this unrelated site"


def test_ordinary_update_does_not_initialize_an_empty_host(host):
    legacy = host[0] / "current/infrastructure/nginx"
    legacy.mkdir()
    (legacy / "host-site.conf").write_text("already migrated")
    result = install(host)
    assert result.returncode != 0 and "not initialized" in result.stderr
    assert "backup" not in host[5].read_text()
    assert (host[0] / "current").resolve().name == "1.0.0"


def test_ordinary_update_retains_automatic_rollback(host):
    subprocess.run(["vps-gateway-init", "--empty"], env=host[4], check=True)
    old = host[0] / "current/infrastructure"
    (old / "nginx").mkdir()
    (old / "nginx/host-site.conf").write_text("already migrated")
    for name in ("deployment/install-systemd.sh", "backup/restore-data.sh", "backup/restore-postgres.sh"):
        executable(old / "scripts" / name, 'echo "restore $0" >> "$EVENTS"\n')
    result = install(host, FAIL_PHASE="site")
    assert result.returncode != 0
    assert (host[0] / "current").resolve().name == "1.0.0"
    assert "restore-data.sh" in host[5].read_text()
    assert "restore-postgres.sh" in host[5].read_text()
