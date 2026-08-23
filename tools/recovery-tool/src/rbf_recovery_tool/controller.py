from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import time

from .config import Profile
from .sftp_client import connect, download_latest_with_proof
from .verification import verify_encrypted_bundle


def _write_json(sftp, directory: str, filename: str, payload: dict[str, object]) -> None:
    target = PurePosixPath(directory) / filename
    temporary = PurePosixPath(directory) / f".{filename}.{secrets.token_hex(6)}.part"
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    try:
        with sftp.open(temporary.as_posix(), "wb") as handle:
            handle.write(data)
        sftp.rename(temporary.as_posix(), target.as_posix())
    except Exception:
        try:
            sftp.remove(temporary.as_posix())
        except Exception:
            pass
        raise


def _set_names(profile: Profile, password: str) -> set[str]:
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            return {
                str(item.filename)
                for item in sftp.listdir_attr(profile.remote_directory)
                if str(item.filename).startswith("rbf-backup-set-")
                and str(item.filename).endswith(".json")
            }
        finally:
            sftp.close()
    finally:
        client.close()


def request_backup(profile: Profile, *, password: str = "") -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{24,128}", profile.enrollment_id):
        raise RuntimeError("The controller profile has no valid enrollment ID.")
    request_id = secrets.token_urlsafe(24)
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            _write_json(
                sftp,
                "/requests",
                f"{request_id}.json",
                {
                    "schema_version": 1,
                    "kind": "rbf-backup-pull-request",
                    "request_id": request_id,
                    "enrollment_id": profile.enrollment_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "reason": "backup-controller",
                },
            )
        finally:
            sftp.close()
    finally:
        client.close()
    return request_id


def _request_state(profile: Profile, request_id: str, password: str) -> str | None:
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            path = f"/status/{request_id}.json"
            try:
                attributes = sftp.stat(path)
            except OSError:
                return None
            if not stat.S_ISREG(attributes.st_mode) or attributes.st_size > 4096:
                raise RuntimeError("The website returned an invalid backup status file.")
            with sftp.open(path, "rb") as handle:
                payload = json.loads(handle.read(4097).decode("utf-8"))
            if (
                not isinstance(payload, dict)
                or payload.get("kind") != "rbf-backup-pull-status"
                or payload.get("request_id") != request_id
                or payload.get("enrollment_id") != profile.enrollment_id
            ):
                raise RuntimeError("The website returned a mismatched backup status file.")
            return str(payload.get("state") or "")
        finally:
            sftp.close()
    finally:
        client.close()


def _local_verified_bundle(profile: Profile, set_name: str) -> tuple[Path, Path] | None:
    destination = Path(profile.destination_directory)
    set_path = destination / set_name
    state_path = destination / f".{set_name}.verified.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        manifest = json.loads(set_path.read_text(encoding="utf-8"))
        recovery = manifest["artifacts"]["recovery"]
        bundle = destination / str(recovery["filename"])
        if (
            state.get("set_filename") == set_name
            and state.get("set_sha256") == hashlib.sha256(set_path.read_bytes()).hexdigest()
            and bundle.is_file()
        ):
            return bundle, set_path
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return None


def _remember_verified(set_manifest: Path) -> None:
    state = {
        "schema_version": 1,
        "set_filename": set_manifest.name,
        "set_sha256": hashlib.sha256(set_manifest.read_bytes()).hexdigest(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    temporary = set_manifest.parent / f".{secrets.token_hex(8)}.verified.tmp"
    temporary.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(set_manifest.parent / f".{set_manifest.name}.verified.json")


def _prune_local(profile: Profile) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=profile.retention_days)
    root = Path(profile.destination_directory)
    allowed = (
        "rbf-backup-set-", "rbf-recovery-", "rbf-postgres-preflight-",
    )
    for path in root.iterdir():
        try:
            if (
                path.is_file()
                and (path.name.startswith(allowed) or path.name.endswith(".verified.json"))
                and datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < cutoff
            ):
                path.unlink()
        except FileNotFoundError:
            continue


def _acknowledge(
    profile: Profile, set_manifest: Path, *, password: str = ""
) -> None:
    digest = hashlib.sha256(set_manifest.read_bytes()).hexdigest()
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            _write_json(
                sftp,
                "/acknowledgements",
                f"{set_manifest.name}.ack.json",
                {
                    "schema_version": 1,
                    "kind": "rbf-backup-pull-acknowledgement",
                    "enrollment_id": profile.enrollment_id,
                    "set_filename": set_manifest.name,
                    "set_sha256": digest,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        finally:
            sftp.close()
    finally:
        client.close()


def sync_latest(
    profile: Profile,
    *,
    password: str = "",
    trigger: bool = False,
    allow_empty: bool = False,
    timeout_seconds: int = 4 * 60 * 60,
) -> Path | None:
    before = _set_names(profile, password) if trigger else set()
    if trigger:
        request_id = request_backup(profile, password=password)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if _set_names(profile, password) - before:
                break
            if _request_state(profile, request_id, password) == "failed":
                raise RuntimeError(
                    "The website reported that the requested backup failed; review its protected host log."
                )
            time.sleep(10)
        else:
            raise RuntimeError("The website did not publish the requested backup in time.")
    available = _set_names(profile, password)
    if not available:
        if allow_empty:
            return None
        raise RuntimeError("The website has not published a committed backup yet.")
    bundle: Path | None = None
    for set_name in sorted(available):
        local = _local_verified_bundle(profile, set_name)
        if local is not None:
            bundle, set_manifest = local
        else:
            bundle, set_manifest = download_latest_with_proof(
                profile, password=password, set_filename=set_name
            )
            verify_encrypted_bundle(bundle, Path(profile.age_identity_path))
            _remember_verified(set_manifest)
        _acknowledge(profile, set_manifest, password=password)
    _prune_local(profile)
    if bundle is None:
        raise RuntimeError("No complete backup set was available.")
    return bundle
