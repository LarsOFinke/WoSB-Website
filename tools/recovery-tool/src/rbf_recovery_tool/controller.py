from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import time

from .config import Profile, TARGETS
from .sftp_client import connect, download_latest_with_proof
from .verification import verify_encrypted_bundle


_SET_NAME_RE = re.compile(r"^rbf-backup-set-\d{8}T\d{6}Z-\d+\.json$")


def _validate_profile(profile: Profile) -> None:
    if profile.target not in TARGETS:
        raise RuntimeError("The recovery profile is not bound to test or production.")
    try:
        profile.validate_target(profile.target)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc


def _newest_set(names: set[str]) -> str | None:
    valid = [name for name in names if _SET_NAME_RE.fullmatch(name)]
    return max(valid) if valid else None


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
    _validate_profile(profile)
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            try:
                entries = sftp.listdir_attr(profile.remote_directory)
            except Exception as exc:
                raise RuntimeError(
                    f"SFTP could not list {profile.target} export directory "
                    f"{profile.remote_directory}: {exc}"
                ) from exc
            return {
                str(item.filename)
                for item in entries
                if _SET_NAME_RE.fullmatch(str(item.filename))
            }
        finally:
            sftp.close()
    finally:
        client.close()


def request_backup(profile: Profile, *, password: str = "") -> str:
    _validate_profile(profile)
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
                    "deployment_environment": profile.target,
                    "requested_controller_username": profile.username,
                    "requested_storage_directory": f"/backups/wosb/{profile.target}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "reason": "backup-controller",
                },
            )
        finally:
            sftp.close()
    finally:
        client.close()
    return request_id


def _request_state(
    profile: Profile, request_id: str, password: str
) -> dict[str, object] | None:
    _validate_profile(profile)
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
                or payload.get("deployment_environment") != profile.target
            ):
                raise RuntimeError("The website returned a mismatched backup status file.")
            return payload
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
    _validate_profile(profile)
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
                    "deployment_environment": profile.target,
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
    _validate_profile(profile)
    before = _set_names(profile, password) if trigger else set()
    requested_set_name: str | None = None
    requested_set_sha256: str | None = None
    if trigger:
        request_id = request_backup(profile, password=password)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            available_after_request = _set_names(profile, password)
            new_sets = available_after_request - before
            request_status = _request_state(profile, request_id, password)
            if request_status and request_status.get("state") == "failed":
                raise RuntimeError(
                    "The website reported that the requested backup failed; review its protected host log."
                )
            reported_set = str((request_status or {}).get("set_filename") or "")
            reported_sha256 = str((request_status or {}).get("set_sha256") or "")
            if (
                request_status
                and request_status.get("state") == "succeeded"
                and reported_set in new_sets
                and re.fullmatch(r"[0-9a-f]{64}", reported_sha256)
            ):
                requested_set_name = reported_set
                requested_set_sha256 = reported_sha256
                break
            time.sleep(10)
        else:
            raise RuntimeError("The website did not publish the requested backup in time.")
    available = _set_names(profile, password)
    if not available:
        if allow_empty:
            return None
        raise RuntimeError("The website has not published a committed backup yet.")
    set_name = requested_set_name or _newest_set(available)
    if set_name is None:
        raise RuntimeError("The website has not published a valid committed backup set.")
    local = _local_verified_bundle(profile, set_name)
    if local is not None:
        bundle, set_manifest = local
    else:
        bundle, set_manifest = download_latest_with_proof(
            profile,
            password=password,
            set_filename=requested_set_name,
        )
        verify_encrypted_bundle(bundle, Path(profile.age_identity_path))
        _remember_verified(set_manifest)
    if requested_set_sha256 and hashlib.sha256(set_manifest.read_bytes()).hexdigest() != requested_set_sha256:
        raise RuntimeError("The website reported a backup set digest that does not match the downloaded manifest.")
    _acknowledge(profile, set_manifest, password=password)
    _prune_local(profile)
    if bundle is None:
        raise RuntimeError("No complete backup set was available.")
    return bundle
