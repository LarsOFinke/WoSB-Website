#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
MIGRATIONS = BACKEND / "migrations" / "versions"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.recovery.contract import MigrationGraph  # noqa: E402


def run(command: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if result.returncode != expect:
        raise RuntimeError(
            f"Command failed ({result.returncode}, expected {expect}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def plain_url(value: str) -> str:
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def database_url(base: str, database: str) -> str:
    # str(URL) intentionally masks credentials as ``***``. This URL is passed
    # directly to psycopg, so retain the actual password for the CI connection.
    return make_url(base).set(database=database).render_as_string(hide_password=False)


def admin_database(base: str) -> str:
    return plain_url(database_url(base, "postgres"))


def recreate_database(base: str, name: str) -> None:
    with psycopg.connect(admin_database(base), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
            cursor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))


def drop_database(base: str, name: str) -> None:
    with psycopg.connect(admin_database(base), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


def linear_revision(graph: MigrationGraph, distance_from_head: int = 5) -> str:
    if len(graph.heads) != 1:
        raise RuntimeError("Recovery matrix currently requires one linear Alembic head.")
    revision = graph.heads[0]
    for _ in range(distance_from_head):
        parents = graph.parents[revision]
        if not parents:
            break
        if len(parents) != 1:
            raise RuntimeError("Recovery matrix encountered a branched migration path.")
        revision = parents[0]
    return revision


def write_env(path: Path, url: str, state: Path) -> None:
    state.mkdir(parents=True, exist_ok=True)
    (state / "uploads").mkdir(exist_ok=True)
    (state / "control/inbox").mkdir(parents=True, exist_ok=True)
    (state / "control/status").mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "APP_ENV=staging",
                f"DATABASE_URL={url}",
                "DB_SCHEMA_MODE=migrate",
                f"UPLOAD_DIR={state / 'uploads'}",
                f"CONTROL_REQUEST_DIR={state / 'control/inbox'}",
                f"CONTROL_STATUS_DIR={state / 'control/status'}",
                "CORS_ORIGINS=http://127.0.0.1",
                "SESSION_COOKIE_SECURE=false",
                "AUTO_SEED=false",
                "WEBHOOK_ENCRYPTION_KEYS=5QvTF9EYs8uK9QjQ0YJ8p1Kfquhy2z9bMv8D4tY6asE=",
                "",
            ]
        ),
        encoding="utf-8",
    )


def backend_env(env_file: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["RBF_ENV_FILE"] = str(env_file)
    env["PYTHONPATH"] = str(BACKEND / "src")
    return env


def free_port() -> int:
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def readiness_check(env: dict[str, str]) -> None:
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--app-dir", "src", "--host", "127.0.0.1", "--port", str(port), "--no-proxy-headers"],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 30
        last_error = ""
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError(f"API exited before readiness:\n{output}")
            try:
                with urlopen(f"http://127.0.0.1:{port}/api/health/ready", timeout=2) as response:
                    if response.status == 200:
                        return
            except Exception as exc:  # readiness polling intentionally tolerates startup races
                last_error = str(exc)
            time.sleep(0.5)
        output = process.stdout.read() if process.stdout else ""
        raise RuntimeError(f"API readiness timed out ({last_error}).\n{output}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser(description="Exercise old-schema backup, restore, migration and API readiness.")
    parser.add_argument("--database-url", default=os.environ.get("RECOVERY_MATRIX_DATABASE_URL", ""))
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("Set RECOVERY_MATRIX_DATABASE_URL or pass --database-url.")
    for command in ("pg_dump", "psql"):
        if shutil.which(command) is None:
            raise SystemExit(f"Required PostgreSQL client command is missing: {command}")

    graph = MigrationGraph.from_directory(MIGRATIONS)
    old_revision = linear_revision(graph)
    suffix = str(os.getpid())
    source_db = f"rbf_recovery_source_{suffix}"
    target_db = f"rbf_recovery_target_{suffix}"
    source_created = False
    target_created = False

    with tempfile.TemporaryDirectory(prefix="rbf-recovery-matrix-") as temporary:
        temp = Path(temporary)
        source_url = database_url(args.database_url, source_db)
        target_url = database_url(args.database_url, target_db)
        source_env_file = temp / "source.env"
        target_env_file = temp / "target.env"
        write_env(source_env_file, source_url, temp / "source-state")
        write_env(target_env_file, target_url, temp / "target-state")
        source_env = backend_env(source_env_file)
        target_env = backend_env(target_env_file)
        dump = temp / "old-schema.sql"

        try:
            recreate_database(args.database_url, source_db)
            source_created = True
            recreate_database(args.database_url, target_db)
            target_created = True
            run([sys.executable, "-m", "alembic", "upgrade", old_revision], cwd=BACKEND, env=source_env)
            with psycopg.connect(plain_url(source_url)) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("CREATE TABLE rbf_recovery_matrix_marker (id integer PRIMARY KEY, value text NOT NULL)")
                    cursor.execute("INSERT INTO rbf_recovery_matrix_marker (id, value) VALUES (1, 'survives-restore-and-migration')")
                connection.commit()

            with dump.open("wb") as output:
                result = subprocess.run(["pg_dump", "--no-owner", "--no-privileges", plain_url(source_url)], stdout=output, stderr=subprocess.PIPE, check=False)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))

            checksum = run(["sha256sum", dump.name], cwd=temp).stdout.split()[0]
            Path(f"{dump}.sha256").write_text(f"{checksum}  {dump.name}\n", encoding="ascii")
            metadata = {
                "schema_version": 2,
                "created_at": "2026-08-01T00:00:00+00:00",
                "backup": {
                    "filename": dump.name,
                    "size_bytes": dump.stat().st_size,
                    "sha256": checksum,
                    "reason": "ci-recovery-matrix",
                    "format": "postgresql-plain-sql",
                    "consistency": "no-running-api",
                },
                "application": {"version": "ci", "git_commit": "ci", "alembic_revisions": [old_revision]},
                "database": {"postgres_version": "ci"},
                "security": {"secret_key_fingerprints": [], "secret_key_count": 0},
            }
            metadata_path = Path(f"{dump}.restore.json")
            metadata_path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")

            compatibility = run(
                [sys.executable, str(REPO_ROOT / "infrastructure/scripts/backup/recovery_preflight.py"), "--metadata", str(metadata_path), "--migrations-dir", str(MIGRATIONS)],
                cwd=REPO_ROOT,
            )
            assessment = json.loads(compatibility.stdout)["assessment"]
            if assessment["status"] != "upgrade" or assessment["migration_required"] is not True:
                raise RuntimeError(f"Expected forward-migration assessment, got: {assessment}")

            future = json.loads(json.dumps(metadata))
            future["application"]["alembic_revisions"] = ["9999_future_revision"]
            future_path = temp / "future.restore.json"
            future_path.write_text(json.dumps(future), encoding="utf-8")
            run(
                [sys.executable, str(REPO_ROOT / "infrastructure/scripts/backup/recovery_preflight.py"), "--metadata", str(future_path), "--migrations-dir", str(MIGRATIONS)],
                cwd=REPO_ROOT,
                expect=2,
            )

            run(["psql", "-v", "ON_ERROR_STOP=1", "-1", plain_url(target_url), "-f", str(dump)])
            run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=target_env)
            run([sys.executable, "-m", "alembic", "check"], cwd=BACKEND, env=target_env)
            run([sys.executable, "-m", "app.db.restore_preflight"], cwd=BACKEND, env=target_env)
            with psycopg.connect(plain_url(target_url)) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT value FROM rbf_recovery_matrix_marker WHERE id = 1")
                    row = cursor.fetchone()
            if row != ("survives-restore-and-migration",):
                raise RuntimeError("Marker data did not survive dump, restore and migration.")
            readiness_check(target_env)

            tampered = temp / "tampered.sql"
            shutil.copy2(dump, tampered)
            tampered.write_bytes(tampered.read_bytes() + b"\n-- tampered\n")
            tampered_metadata = json.loads(json.dumps(metadata))
            tampered_metadata["backup"]["filename"] = tampered.name
            tampered_path = Path(f"{tampered}.restore.json")
            tampered_path.write_text(json.dumps(tampered_metadata), encoding="utf-8")
            run(
                [sys.executable, str(REPO_ROOT / "infrastructure/scripts/backup/backup_metadata.py"), "validate", str(tampered_path), str(tampered)],
                cwd=REPO_ROOT,
                expect=1,
            )
        finally:
            if source_created:
                drop_database(args.database_url, source_db)
            if target_created:
                drop_database(args.database_url, target_db)

    print(f"Recovery matrix OK: {old_revision} -> {', '.join(graph.heads)} with data and API readiness.")


if __name__ == "__main__":
    main()
