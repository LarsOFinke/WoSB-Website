from __future__ import annotations

from dataclasses import dataclass
import gzip
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time

from contracts.recovery.contract import (
    MigrationGraph,
    add_report_check,
    assess_compatibility,
    descriptor_from_manifest,
    finalize_report,
    is_production_consistent,
    new_report,
    write_report,
)

from .platform_support import application_data_root
from .verification import extract_postgres_artifact, extract_verified_bundle, verify_sidecar


_POSTGRES_IMAGE = "postgres:16.14-alpine3.24"
_DEFAULT_PORT = 55432
_PROJECT_NAME = "rbf-recovery-lab"


@dataclass(frozen=True)
class LabStatus:
    configured: bool
    docker_available: bool
    running: bool
    healthy: bool
    detail: str


@dataclass(frozen=True)
class LabConnection:
    host: str
    port: int
    database: str
    username: str
    password: str

    @property
    def safe_summary(self) -> str:
        return f"host={self.host} port={self.port} database={self.database} user={self.username}"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass(frozen=True)
class RecoveryVerificationResult:
    report: Path
    recoverable: bool
    compatibility: str
    connection: LabConnection


def lab_root() -> Path:
    return application_data_root() / "RBF Recovery Tool" / "db-lab"


def compose_path() -> Path:
    return lab_root() / "compose.yaml"


def env_path() -> Path:
    return lab_root() / ".env"


def _docker() -> str:
    executable = shutil.which("docker")
    if not executable:
        raise RuntimeError("Docker wurde nicht gefunden.")
    return executable


def _docker_base() -> list[str]:
    executable = _docker()
    context = subprocess.run(
        [executable, "context", "inspect", "rootless"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
    )
    return [executable, "--context", "rootless"] if context.returncode == 0 else [executable]


def _compose_command(*arguments: str, overrides: tuple[Path, ...] = ()) -> list[str]:
    command = [
        *_docker_base(), "compose", "--project-name", _PROJECT_NAME,
        "--project-directory", str(lab_root()), "--env-file", str(env_path()),
        "-f", str(compose_path()),
    ]
    for override in overrides:
        command.extend(("-f", str(override)))
    return [*command, *arguments]


def _run(command: list[str], *, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        suffix = f" ({detail[-1]})" if detail else ""
        raise RuntimeError(f"Befehl fehlgeschlagen{suffix}.")
    return result


def docker_available() -> bool:
    try:
        result = _run([*_docker_base(), "info", "--format", "{{json .SecurityOptions}}"], timeout=20, check=False)
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def docker_is_rootless() -> bool:
    try:
        result = _run([*_docker_base(), "info", "--format", "{{json .SecurityOptions}}"], timeout=20, check=False)
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and "rootless" in result.stdout.casefold()


def _read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path().is_file():
        return values
    for raw_line in env_path().read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def initialize_lab(port: int = _DEFAULT_PORT) -> LabConnection:
    if not 1024 <= int(port) <= 65535:
        raise ValueError("Der lokale PostgreSQL-Port muss zwischen 1024 und 65535 liegen.")
    root = lab_root()
    root.mkdir(parents=True, exist_ok=True)
    try: os.chmod(root, 0o700)
    except OSError: pass
    values = _read_env()
    password = values.get("POSTGRES_PASSWORD") or secrets.token_urlsafe(36)
    username = values.get("POSTGRES_USER") or "rbf_recovery"
    database = values.get("POSTGRES_DB") or "rbf_recovery"
    configured_port = int(values.get("POSTGRES_LOCAL_PORT") or port)
    env_payload = (
        f"POSTGRES_USER={username}\nPOSTGRES_PASSWORD={password}\n"
        f"POSTGRES_DB={database}\nPOSTGRES_LOCAL_PORT={configured_port}\n"
    )
    temporary_env = env_path().with_name(".env.tmp")
    temporary_env.write_text(env_payload, encoding="utf-8")
    os.chmod(temporary_env, 0o600)
    os.replace(temporary_env, env_path())
    compose_payload = f'''services:
  postgres:
    image: {_POSTGRES_IMAGE}
    restart: unless-stopped
    environment:
      POSTGRES_USER: "${{POSTGRES_USER}}"
      POSTGRES_PASSWORD: "${{POSTGRES_PASSWORD}}"
      POSTGRES_DB: "${{POSTGRES_DB}}"
    ports:
      - "127.0.0.1:${{POSTGRES_LOCAL_PORT}}:5432"
    volumes:
      - rbf_recovery_postgres:/var/lib/postgresql/data
    networks:
      - rbf_recovery_backend
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,nodev,size=64m
      - /var/run/postgresql:rw,nosuid,nodev,size=16m
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test:
        - CMD-SHELL
        - 'pg_isready -U "$${{POSTGRES_USER}}" -d "$${{POSTGRES_DB}}"'
      interval: 5s
      timeout: 5s
      retries: 24
      start_period: 10s
    logging:
      driver: local
      options:
        max-size: "10m"
        max-file: "3"

networks:
  rbf_recovery_backend:
    name: rbf-recovery-lab-backend
    internal: true

volumes:
  rbf_recovery_postgres:
    name: rbf-recovery-lab-postgres
'''
    temporary_compose = compose_path().with_name("compose.yaml.tmp")
    temporary_compose.write_text(compose_payload, encoding="utf-8")
    os.chmod(temporary_compose, 0o600)
    os.replace(temporary_compose, compose_path())
    return LabConnection("127.0.0.1", configured_port, database, username, password)


def connection() -> LabConnection:
    values = _read_env()
    required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_LOCAL_PORT")
    if not all(values.get(key) for key in required):
        raise RuntimeError("Das lokale Recovery-Labor ist noch nicht initialisiert.")
    return LabConnection("127.0.0.1", int(values["POSTGRES_LOCAL_PORT"]), values["POSTGRES_DB"], values["POSTGRES_USER"], values["POSTGRES_PASSWORD"])


def lab_status() -> LabStatus:
    configured = compose_path().is_file() and env_path().is_file()
    available = docker_available()
    if not configured: return LabStatus(False, available, False, False, "Nicht eingerichtet")
    if not available: return LabStatus(True, False, False, False, "Docker nicht verfügbar")
    result = _run(_compose_command("ps", "--format", "json"), timeout=30, check=False)
    output = (result.stdout or "").casefold()
    running = result.returncode == 0 and "running" in output
    healthy = running and "healthy" in output
    return LabStatus(True, True, running, healthy, "Gesund" if healthy else ("Gestartet" if running else "Gestoppt"))


def start_lab() -> LabConnection:
    if not compose_path().is_file(): initialize_lab()
    if not docker_available(): raise RuntimeError("Docker ist nicht erreichbar. Richte zuerst rootless Docker ein.")
    _run(_compose_command("pull", "postgres"), timeout=1800)
    _run(_compose_command("up", "-d", "postgres"), timeout=300)
    wait_until_healthy()
    return connection()


def stop_lab() -> None:
    if compose_path().is_file() and docker_available(): _run(_compose_command("stop", "postgres"), timeout=120)


def remove_lab_data() -> None:
    if compose_path().is_file() and docker_available(): _run(_compose_command("down", "--volumes", "--remove-orphans"), timeout=300)


def wait_until_healthy(timeout: int = 180) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if lab_status().healthy: return
        time.sleep(2)
    raise RuntimeError("Das lokale PostgreSQL-Labor wurde nicht rechtzeitig bereit.")


def _exec_postgres(*arguments: str, input_stream=None, timeout: int = 600) -> None:
    process = subprocess.Popen(_compose_command("exec", "-T", "postgres", *arguments), stdin=input_stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    try: stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill(); process.communicate()
        raise RuntimeError("Der lokale PostgreSQL-Vorgang hat das Zeitlimit überschritten.")
    if process.returncode != 0:
        detail = (stderr or stdout or b"").decode("utf-8", errors="replace").strip().splitlines()
        raise RuntimeError(f"Lokaler PostgreSQL-Vorgang fehlgeschlagen{f' ({detail[-1]})' if detail else ''}.")


def restore_dump(dump: Path) -> LabConnection:
    dump = dump.expanduser().resolve()
    if not dump.is_file() or not (dump.name.endswith(".sql") or dump.name.endswith(".sql.gz")):
        raise RuntimeError("Es wird ein regulärer .sql- oder .sql.gz-Dump benötigt.")
    details = start_lab()
    _exec_postgres("dropdb", "--if-exists", "--force", "-U", details.username, details.database, timeout=120)
    _exec_postgres("createdb", "-U", details.username, "-O", details.username, details.database, timeout=120)
    opener = gzip.open if dump.name.endswith(".gz") else open
    with opener(dump, "rb") as source:
        _exec_postgres("psql", "-v", "ON_ERROR_STOP=1", "-U", details.username, "-d", details.database, input_stream=source, timeout=3600)
    _exec_postgres("psql", "-v", "ON_ERROR_STOP=1", "-U", details.username, "-d", details.database, "-c", "SELECT 1;", timeout=120)
    return details


def _artifact_binding(path: Path) -> dict[str, object]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"filename": path.name, "size_bytes": path.stat().st_size, "sha256": digest}


def import_check_bundle(bundle: Path, identity: Path, report_path: Path) -> RecoveryVerificationResult:
    bundle = bundle.expanduser().resolve(); identity = identity.expanduser().resolve(); report_path = report_path.expanduser().resolve()
    report = new_report(mode="import-check", source=str(bundle), source_artifact=_artifact_binding(bundle))
    try:
        verify_sidecar(bundle)
        add_report_check(report, name="bundle_integrity", status="passed", detail="Encrypted bundle checksum and manifest inventory are verified during extraction.")
        with tempfile.TemporaryDirectory(prefix="rbf-import-check-") as temporary:
            dump = extract_postgres_artifact(bundle, identity, Path(temporary))
            details = restore_dump(dump)
        add_report_check(report, name="postgres_import", status="passed", detail="PostgreSQL imported the dump and SELECT 1 succeeded.")
        add_report_check(report, name="runtime_recovery", status="skipped", detail="Import checks do not execute migrations or start the application.")
        finalize_report(report, status="passed", recoverable=False)
        write_report(report_path, report)
        return RecoveryVerificationResult(report_path, False, "import-only", details)
    except Exception as exc:
        add_report_check(report, name="import_check", status="failed", detail=str(exc))
        finalize_report(report, status="failed", recoverable=False)
        write_report(report_path, report)
        raise


def _application_preflight_override(image: str, recovered_env: Path, details: LabConnection) -> str:
    database_url = f"postgresql+psycopg://{details.username}:{details.password}@postgres:5432/{details.database}"
    return f'''services:
  recovery-migrate:
    image: {image}
    env_file:
      - {json.dumps(str(recovered_env))}
    environment:
      DATABASE_URL: {json.dumps(database_url)}
      DB_SCHEMA_MODE: migrate
      APP_ENV: production
      RBF_ENV_FILE: /run/rbf-preflight.env
      UPLOAD_DIR: /data/uploads
      CONTROL_REQUEST_DIR: /tmp/control/inbox
      CONTROL_STATUS_DIR: /tmp/control/status
    volumes:
      - {json.dumps(str(recovered_env) + ":/run/rbf-preflight.env:ro")}
    command: ["sh", "-euc", "alembic upgrade head && alembic check && python -m app.db.restore_preflight"]
    networks: [rbf_recovery_backend]
    read_only: true
    tmpfs: [/tmp, /data/uploads]
    security_opt: ["no-new-privileges:true"]
  recovery-api:
    image: {image}
    env_file:
      - {json.dumps(str(recovered_env))}
    environment:
      DATABASE_URL: {json.dumps(database_url)}
      DB_SCHEMA_MODE: migrate
      APP_ENV: production
      RBF_ENV_FILE: /run/rbf-preflight.env
      UPLOAD_DIR: /data/uploads
      CONTROL_REQUEST_DIR: /tmp/control/inbox
      CONTROL_STATUS_DIR: /tmp/control/status
    volumes:
      - {json.dumps(str(recovered_env) + ":/run/rbf-preflight.env:ro")}
    command: ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
    networks: [rbf_recovery_backend]
    read_only: true
    tmpfs: [/tmp, /data/uploads]
    security_opt: ["no-new-privileges:true"]
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=4)"]
      interval: 3s
      timeout: 5s
      retries: 30
      start_period: 5s
'''


def verify_recovery(
    bundle: Path,
    identity: Path,
    repository: Path,
    report_path: Path,
    *,
    allow_legacy: bool = False,
    allow_uncoordinated: bool = False,
) -> RecoveryVerificationResult:
    bundle = bundle.expanduser().resolve(); identity = identity.expanduser().resolve(); repository = repository.expanduser().resolve(); report_path = report_path.expanduser().resolve()
    backend = repository / "backend"
    migrations = backend / "migrations/versions"
    if not (backend / "Dockerfile").is_file() or not migrations.is_dir():
        raise RuntimeError("Das angegebene Repository enthält kein vollständiges WoSB-Backend.")
    report = new_report(mode="recovery-verify", source=str(bundle), source_artifact=_artifact_binding(bundle))
    compatibility_status = "unknown"
    details = initialize_lab()
    override: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="rbf-full-recovery-") as temporary:
            extracted, manifest = extract_verified_bundle(bundle, identity, Path(temporary) / "bundle")
            add_report_check(report, name="bundle_integrity", status="passed", detail="Encrypted bundle, sidecar, safe paths and manifest inventory are valid.")
            artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
            if not isinstance(artifacts, dict): raise RuntimeError("Recovery manifest has no artifacts mapping.")
            dump = extracted / str(artifacts.get("postgres") or "")
            metadata = Path(f"{dump}.restore.json")
            if metadata.is_file():
                payload = json.loads(metadata.read_text(encoding="utf-8"))
                descriptor = descriptor_from_manifest(payload)
                assessment = assess_compatibility(descriptor, MigrationGraph.from_directory(migrations), allow_unrecorded=allow_legacy)
                compatibility_status = assessment.status
                if not assessment.compatible: raise RuntimeError(assessment.detail)
                if not is_production_consistent(descriptor) and not allow_uncoordinated:
                    raise RuntimeError("Das Backup besitzt keinen produktiven Konsistenznachweis.")
                add_report_check(report, name="metadata_compatibility", status="passed", detail=assessment.detail, data={"assessment": assessment.to_dict(), "descriptor": descriptor.to_dict()})
            elif allow_legacy:
                add_report_check(report, name="metadata_compatibility", status="warning", detail="Legacy bundle without restore metadata was explicitly accepted.")
                compatibility_status = "legacy"
            else:
                raise RuntimeError("Restore-Metadaten fehlen; verwende nur im Notfall --allow-legacy.")
            details = restore_dump(dump)
            add_report_check(report, name="staging_database_creation", status="passed", detail="Rootless isolated PostgreSQL lab is running.")
            add_report_check(report, name="postgres_import", status="passed", detail="Dump import and SQL probe succeeded.")
            recovered_env = extracted / "configuration/infrastructure.env"
            if not recovered_env.is_file(): raise RuntimeError("Recovery bundle has no infrastructure.env.")
            image = f"rbf-recovery-preflight:{hashlib.sha256(str(repository).encode()).hexdigest()[:12]}"
            _run([*_docker_base(), "build", "--pull", "-t", image, str(backend)], timeout=3600)
            override = lab_root() / "preflight.compose.yaml"
            override.write_text(_application_preflight_override(image, recovered_env, details), encoding="utf-8")
            try: os.chmod(override, 0o600)
            except OSError: pass
            _run(_compose_command("run", "--rm", "recovery-migrate", overrides=(override,)), timeout=3600)
            add_report_check(report, name="migration_and_schema_preflight", status="passed", detail="Alembic upgrade head and alembic check succeeded using the current backend image.")
            add_report_check(report, name="secret_key_preflight", status="passed", detail="Encrypted application records are readable with the recovered key ring.")
            _run(_compose_command("up", "-d", "recovery-api", overrides=(override,)), timeout=300)
            deadline = time.monotonic() + 180
            healthy = False
            while time.monotonic() < deadline:
                status = _run(_compose_command("ps", "--format", "json", "recovery-api", overrides=(override,)), timeout=30, check=False)
                if "healthy" in (status.stdout or "").casefold(): healthy = True; break
                time.sleep(3)
            if not healthy:
                logs = _run(_compose_command("logs", "--no-color", "recovery-api", overrides=(override,)), timeout=60, check=False)
                raise RuntimeError(f"API readiness failed: {(logs.stdout or logs.stderr or '').strip()[-1000:]}")
            add_report_check(report, name="application_readiness_preflight", status="passed", detail="Current API image reached readiness inside an internal network without published ports.")
            _run(_compose_command("rm", "-s", "-f", "recovery-api", overrides=(override,)), timeout=120, check=False)
            add_report_check(report, name="preflight_cleanup", status="passed", detail="Temporary application preflight container was removed; lab remains available for inspection.")
        finalize_report(report, status="passed", recoverable=True)
        write_report(report_path, report)
        return RecoveryVerificationResult(report_path, True, compatibility_status, details)
    except Exception as exc:
        add_report_check(report, name="recovery_verify", status="failed", detail=str(exc))
        finalize_report(report, status="failed", recoverable=False)
        write_report(report_path, report)
        raise
    finally:
        if override is not None:
            _run(_compose_command("rm", "-s", "-f", "recovery-api", overrides=(override,)), timeout=120, check=False)
            override.unlink(missing_ok=True)


def restore_bundle(bundle: Path, identity: Path) -> LabConnection:
    with tempfile.TemporaryDirectory(prefix="rbf-db-lab-") as temporary:
        dump = extract_postgres_artifact(bundle, identity, Path(temporary))
        return restore_dump(dump)
