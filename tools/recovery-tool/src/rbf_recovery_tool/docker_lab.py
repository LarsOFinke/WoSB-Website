from __future__ import annotations

from dataclasses import dataclass
import gzip
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time

from .platform_support import application_data_root
from .verification import extract_postgres_artifact


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
        return (
            f"host={self.host} port={self.port} "
            f"database={self.database} user={self.username}"
        )

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


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


def _compose_command(*arguments: str) -> list[str]:
    return [
        *_docker_base(),
        "compose",
        "--project-name",
        _PROJECT_NAME,
        "--project-directory",
        str(lab_root()),
        "--env-file",
        str(env_path()),
        "-f",
        str(compose_path()),
        *arguments,
    ]


def _run(command: list[str], *, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        suffix = f" ({detail[-1]})" if detail else ""
        raise RuntimeError(f"Befehl fehlgeschlagen{suffix}.")
    return result


def docker_available() -> bool:
    try:
        result = _run(
            [*_docker_base(), "info", "--format", "{{json .SecurityOptions}}"],
            timeout=20,
            check=False,
        )
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def docker_is_rootless() -> bool:
    try:
        result = _run(
            [*_docker_base(), "info", "--format", "{{json .SecurityOptions}}"],
            timeout=20,
            check=False,
        )
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
    try:
        os.chmod(root, 0o700)
    except OSError:
        pass

    values = _read_env()
    password = values.get("POSTGRES_PASSWORD") or secrets.token_urlsafe(36)
    username = values.get("POSTGRES_USER") or "rbf_recovery"
    database = values.get("POSTGRES_DB") or "rbf_recovery"
    configured_port = int(values.get("POSTGRES_LOCAL_PORT") or port)
    env_payload = (
        f"POSTGRES_USER={username}\n"
        f"POSTGRES_PASSWORD={password}\n"
        f"POSTGRES_DB={database}\n"
        f"POSTGRES_LOCAL_PORT={configured_port}\n"
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
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,nodev,size=64m
      - /var/run/postgresql:rw,nosuid,nodev,size=16m
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \"$${{POSTGRES_USER}}\" -d \"$${{POSTGRES_DB}}\""]
      interval: 5s
      timeout: 5s
      retries: 24
      start_period: 10s
    logging:
      driver: local
      options:
        max-size: "10m"
        max-file: "3"

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
    return LabConnection(
        host="127.0.0.1",
        port=int(values["POSTGRES_LOCAL_PORT"]),
        database=values["POSTGRES_DB"],
        username=values["POSTGRES_USER"],
        password=values["POSTGRES_PASSWORD"],
    )


def lab_status() -> LabStatus:
    configured = compose_path().is_file() and env_path().is_file()
    available = docker_available()
    if not configured:
        return LabStatus(False, available, False, False, "Nicht eingerichtet")
    if not available:
        return LabStatus(True, False, False, False, "Docker nicht verfügbar")
    result = _run(
        _compose_command("ps", "--format", "json"),
        timeout=30,
        check=False,
    )
    output = (result.stdout or "").casefold()
    running = result.returncode == 0 and "running" in output
    healthy = running and "healthy" in output
    detail = "Gesund" if healthy else ("Gestartet" if running else "Gestoppt")
    return LabStatus(True, True, running, healthy, detail)


def start_lab() -> LabConnection:
    if not compose_path().is_file():
        initialize_lab()
    if not docker_available():
        raise RuntimeError("Docker ist nicht erreichbar. Richte zuerst rootless Docker ein.")
    _run(_compose_command("pull", "postgres"), timeout=1800)
    _run(_compose_command("up", "-d", "postgres"), timeout=300)
    wait_until_healthy()
    return connection()


def stop_lab() -> None:
    if compose_path().is_file() and docker_available():
        _run(_compose_command("stop", "postgres"), timeout=120)


def remove_lab_data() -> None:
    if compose_path().is_file() and docker_available():
        _run(_compose_command("down", "--volumes", "--remove-orphans"), timeout=300)


def wait_until_healthy(timeout: int = 180) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = lab_status()
        if status.healthy:
            return
        time.sleep(2)
    raise RuntimeError("Das lokale PostgreSQL-Labor wurde nicht rechtzeitig bereit.")


def _exec_postgres(*arguments: str, input_stream=None, timeout: int = 600) -> None:
    command = _compose_command("exec", "-T", "postgres", *arguments)
    process = subprocess.Popen(
        command,
        stdin=input_stream,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise RuntimeError("Der lokale PostgreSQL-Vorgang hat das Zeitlimit überschritten.")
    if process.returncode != 0:
        detail = (stderr or stdout or b"").decode("utf-8", errors="replace").strip().splitlines()
        suffix = f" ({detail[-1]})" if detail else ""
        raise RuntimeError(f"Lokaler PostgreSQL-Vorgang fehlgeschlagen{suffix}.")


def restore_dump(dump: Path) -> LabConnection:
    dump = dump.expanduser().resolve()
    if not dump.is_file() or not (
        dump.name.endswith(".sql") or dump.name.endswith(".sql.gz")
    ):
        raise RuntimeError("Es wird ein regulärer .sql- oder .sql.gz-Dump benötigt.")
    details = start_lab()
    _exec_postgres(
        "dropdb", "--if-exists", "--force", "-U", details.username, details.database,
        timeout=120,
    )
    _exec_postgres(
        "createdb", "-U", details.username, "-O", details.username, details.database,
        timeout=120,
    )
    opener = gzip.open if dump.name.endswith(".gz") else open
    with opener(dump, "rb") as source:
        _exec_postgres(
            "psql", "-v", "ON_ERROR_STOP=1", "-U", details.username, "-d", details.database,
            input_stream=source,
            timeout=3600,
        )
    _exec_postgres(
        "psql", "-v", "ON_ERROR_STOP=1", "-U", details.username, "-d", details.database,
        "-c", "SELECT 1;",
        timeout=120,
    )
    return details


def restore_bundle(bundle: Path, identity: Path) -> LabConnection:
    with tempfile.TemporaryDirectory(prefix="rbf-db-lab-") as temporary:
        dump = extract_postgres_artifact(bundle, identity, Path(temporary))
        return restore_dump(dump)
