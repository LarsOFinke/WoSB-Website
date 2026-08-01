from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from contracts.backup_enrollment import (
    RESPONSE_KIND,
    SCHEMA_VERSION,
    canonical_json,
    validate_request,
    validate_response,
)

from .config import Profile, profile_path, save_profile
from .linux_setup import support_script
from .verification import generate_identity


def _load_request(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise RuntimeError(f"Enrollment-Anfrage nicht gefunden: {resolved}")
    try:
        content = resolved.read_text(encoding="utf-8-sig")
    except PermissionError as exc:
        raise RuntimeError(f"Keine Leseberechtigung für die Enrollment-Anfrage: {resolved}") from exc
    except OSError as exc:
        raise RuntimeError(f"Enrollment-Anfrage konnte nicht gelesen werden: {resolved}") from exc
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Enrollment-Anfrage ist kein gültiges JSON (Zeile {exc.lineno}, Spalte {exc.colno}): {resolved}"
        ) from exc
    try:
        return validate_request(payload)
    except ValueError as exc:
        raise RuntimeError(f"Ungültige Enrollment-Anfrage in {resolved}: {exc}") from exc


def _public_recipient(identity: Path) -> str:
    for line in identity.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("# public key:"):
            value = line.split(":", 1)[1].strip()
            if value.startswith("age1"):
                return value
    raise RuntimeError("Der öffentliche age-Schlüssel fehlt in der Identitätsdatei.")


def _ensure_recovery_ssh_key(path: Path) -> str:
    if not shutil.which("ssh-keygen"):
        raise RuntimeError("ssh-keygen fehlt; installiere das Paket openssh-client.")
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        completed = subprocess.run(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                "rbf-recovery-local-readonly",
                "-f",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0 or not path.is_file():
            raise RuntimeError("Der lokale Recovery-Leseschlüssel konnte nicht erzeugt werden.")
    os.chmod(path, 0o600)
    completed = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    public_key = completed.stdout.strip()
    if completed.returncode != 0 or not public_key.startswith("ssh-ed25519 "):
        raise RuntimeError("Der lokale Recovery-Leseschlüssel ist ungültig.")
    Path(f"{path}.pub").write_text(
        f"{public_key} rbf-recovery-local-readonly\n",
        encoding="utf-8",
    )
    os.chmod(Path(f"{path}.pub"), 0o644)
    return f"{public_key} rbf-recovery-local-readonly"


def _configure_local_recovery_profile(
    *,
    port: int,
    username: str,
    remote_directory: str,
    ssh_key: Path,
    identity: Path,
    fingerprint: str,
) -> Path:
    from .sftp_client import connect, fetch_host_fingerprint

    profile = Profile(
        host="127.0.0.1",
        port=port,
        username=username,
        remote_directory=remote_directory,
        destination_directory=str(Path.home() / "RBF-Recovery" / "Backups"),
        ssh_key_path=str(ssh_key),
        age_identity_path=str(identity),
        host_fingerprint=fingerprint,
    ).normalized()
    actual = fetch_host_fingerprint(profile)
    if actual != fingerprint:
        raise RuntimeError(
            "Der lokale SSH-Host-Key stimmt nicht mit dem provisionierten Server überein."
        )
    client = connect(profile)
    try:
        sftp = client.open_sftp()
        try:
            sftp.listdir(profile.remote_directory)
        finally:
            sftp.close()
    finally:
        client.close()
    existing = profile_path()
    if existing.is_file():
        backup = existing.with_name(f"{existing.name}.before-server-enrollment")
        shutil.copy2(existing, backup)
        os.chmod(backup, 0o600)
    return save_profile(profile)


def provision_backup_server(
    request_path: Path,
    *,
    host: str,
    output: Path,
    identity: Path,
    port: int = 22,
    username: str = "rbf-backup",
    storage_directory: str = "/srv/rbf-backups/wosb",
    allow_from: str = "",
    skip_package_install: bool = False,
    retention_days: int = 30,
    recovery_username: str = "rbf-recovery",
    recovery_ssh_key: Path = Path.home() / "RBF-Recovery" / "rbf-recovery-readonly-ed25519",
    configure_local_profile: bool = True,
) -> Path:
    if os.name == "nt" or sys.platform == "darwin":
        raise RuntimeError("Die automatische Backup-Server-Provisionierung wird nur unter Linux unterstützt.")
    request = _load_request(request_path.expanduser().resolve())
    requested_username = str(request["requested_username"])
    requested_directory = str(request["requested_directory"])
    if username != requested_username:
        raise RuntimeError(
            f"Der angegebene Upload-Benutzer '{username}' stimmt nicht mit der Enrollment-Anfrage "
            f"'{requested_username}' überein."
        )
    if requested_directory != "/data":
        raise RuntimeError(
            f"Die Enrollment-Anfrage erwartet den nicht unterstützten SFTP-Pfad '{requested_directory}'."
        )
    identity = identity.expanduser().resolve()
    if identity.exists():
        age_recipient = _public_recipient(identity)
    else:
        age_recipient = generate_identity(identity)
    recovery_ssh_key = recovery_ssh_key.expanduser().resolve()
    recovery_public_key = _ensure_recovery_ssh_key(recovery_ssh_key)

    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rbf-backup-server-") as directory:
        result_path = Path(directory) / "provisioning-result.json"
        provisioner = support_script("Provision-RbfBackupServer.sh", require_root_owned=True)
        command = [
            str(provisioner),
            "--request", str(request_path.expanduser().resolve()),
            "--host", host,
            "--port", str(port),
            "--user", username,
            "--directory", storage_directory,
            "--recovery-user", recovery_username,
            "--recovery-public-key", recovery_public_key,
            "--retention-days", str(retention_days),
            "--result", str(result_path),
        ]
        if allow_from:
            command.extend(["--allow-from", allow_from])
        if skip_package_install:
            command.append("--skip-package-install")
        if os.geteuid() != 0:
            pkexec = shutil.which("pkexec")
            if not pkexec:
                raise RuntimeError("pkexec fehlt; führe den Provisioning-Befehl einmalig mit sudo aus.")
            command.insert(0, pkexec)
        completed = subprocess.run(command, check=False, text=True, timeout=1800)
        if completed.returncode != 0 or not result_path.is_file():
            raise RuntimeError("Die Backup-Server-Provisionierung ist fehlgeschlagen.")
        try:
            host_payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Das Provisioning-Ergebnis ist ungültig.") from exc

    if configure_local_profile:
        _configure_local_recovery_profile(
            port=int(host_payload.get("port") or port),
            username=str(host_payload.get("recovery_username") or recovery_username),
            remote_directory=str(host_payload.get("remote_directory") or "/data"),
            ssh_key=recovery_ssh_key,
            identity=identity,
            fingerprint=str(host_payload.get("host_key_fingerprint") or ""),
        )

    response = {
        "schema_version": SCHEMA_VERSION,
        "kind": RESPONSE_KIND,
        "enrollment_id": request["enrollment_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "host": host_payload.get("host"),
        "port": host_payload.get("port"),
        "username": host_payload.get("username"),
        "remote_directory": host_payload.get("remote_directory"),
        "host_key": host_payload.get("host_key"),
        "host_key_fingerprint": host_payload.get("host_key_fingerprint"),
        "age_recipient": age_recipient,
        "managed_server": True,
    }
    try:
        response = validate_response(response, expected_enrollment_id=str(request["enrollment_id"]))
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    temporary.write_text(canonical_json(response), encoding="utf-8")
    if os.name != "nt":
        os.chmod(temporary, 0o600)
    os.replace(temporary, output)
    return output
