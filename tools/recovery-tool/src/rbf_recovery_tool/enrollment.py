from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


RESPONSE_KIND = "rbf-backup-enrollment-response"
REQUEST_KIND = "rbf-backup-enrollment-request"
SCHEMA_VERSION = 1
_HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_REMOTE_RE = re.compile(r"^/[A-Za-z0-9._/-]+$")
_ENROLLMENT_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}$")
_HOST_KEY_RE = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$"
)
_FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{40,64}$")
_AGE_RE = re.compile(r"^age1[0-9a-z]{20,}$")


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return value


def _text(payload: dict[str, Any], key: str, pattern: re.Pattern[str], label: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not pattern.fullmatch(value):
        raise ValueError(f"Invalid {label}.")
    return value


def _remote_directory(payload: dict[str, Any], key: str = "remote_directory") -> str:
    value = _text(payload, key, _REMOTE_RE, key.replace("_", " "))
    value = value.rstrip("/") or "/"
    if any(part in {"", ".", ".."} for part in value.split("/")[1:]):
        raise ValueError("Invalid remote directory path segments.")
    return value


def validate_response(payload: object) -> dict[str, Any]:
    source = _object(payload, "Enrollment response")
    if source.get("kind") == REQUEST_KIND:
        raise ValueError(
            "This file is an enrollment request, not a response. "
            "Run the backup-server provisioning command and select the JSON it creates."
        )
    if source.get("schema_version") != SCHEMA_VERSION or source.get("kind") != RESPONSE_KIND:
        raise ValueError("Unsupported enrollment response schema.")
    try:
        port = int(source.get("port") or 22)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid SSH port.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("Invalid SSH port.")
    enrollment_id = _text(source, "enrollment_id", _ENROLLMENT_RE, "enrollment ID")
    recovery_username = str(source.get("recovery_username") or "").strip()
    if recovery_username and not _USER_RE.fullmatch(recovery_username):
        raise ValueError("Invalid recovery username.")
    managed_server = source.get("managed_server") is True
    environment = str(source.get("deployment_environment") or "").strip().lower()
    if environment not in {"test", "production"}:
        raise ValueError("Invalid deployment environment.")
    remote_directory = _remote_directory(source)
    recovery_directory = (
        _remote_directory(source, "recovery_directory") if managed_server else remote_directory
    )
    trust_model = str(source.get("trust_model") or "").strip()
    if managed_server and trust_model != "server-controlled-ingest-v1":
        raise ValueError("Managed backup server has an unsupported trust model.")
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": RESPONSE_KIND,
        "enrollment_id": enrollment_id,
        "deployment_environment": environment,
        "created_at": str(source.get("created_at") or "").strip(),
        "host": _text(source, "host", _HOST_RE, "backup host"),
        "port": port,
        "username": _text(source, "username", _USER_RE, "SSH username"),
        "recovery_username": recovery_username,
        "storage_directory": _remote_directory(source, "storage_directory"),
        "remote_directory": remote_directory,
        "recovery_directory": recovery_directory,
        "host_key": _text(source, "host_key", _HOST_KEY_RE, "SSH host key"),
        "host_key_fingerprint": _text(
            source, "host_key_fingerprint", _FINGERPRINT_RE, "SSH host-key fingerprint"
        ),
        "age_recipient": _text(source, "age_recipient", _AGE_RE, "age recipient"),
        "managed_server": managed_server,
        "trust_model": trust_model,
    }
    if (
        result["username"],
        result["recovery_username"],
        result["storage_directory"],
    ) != (
        f"rbf-backup-{environment}",
        f"rbf-recovery-{environment}",
        f"/backups/wosb/{environment}",
    ):
        raise ValueError("Enrollment response identity does not match its deployment environment.")
    return result


def load_response(path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise RuntimeError(f"Enrollment response not found: {resolved}")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Enrollment response is not valid JSON: {resolved}") from exc
    try:
        return validate_response(payload)
    except ValueError as exc:
        raise RuntimeError(f"Invalid enrollment response {resolved}: {exc}") from exc


def discover_response(directory: Path | None = None) -> Path:
    root = (directory or (Path.home() / "Downloads")).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"Enrollment response directory not found: {root}")
    valid: list[Path] = []
    requests: list[Path] = []
    invalid_responses: list[tuple[Path, str]] = []
    for candidate in root.glob("*.json"):
        try:
            if not candidate.is_file() or candidate.is_symlink() or candidate.stat().st_size > 1024 * 1024:
                continue
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("kind") == REQUEST_KIND:
            requests.append(candidate)
            continue
        if payload.get("kind") != RESPONSE_KIND:
            continue
        try:
            validate_response(payload)
            valid.append(candidate)
        except ValueError as exc:
            invalid_responses.append((candidate, str(exc)))
    if len(valid) == 1:
        return valid[0]
    if len(valid) > 1:
        names = ", ".join(sorted(path.name for path in valid))
        raise RuntimeError(
            f"Multiple valid enrollment responses were found in {root}: {names}. "
            "Use --response to select the intended target explicitly."
        )
    if invalid_responses:
        candidate, problem = max(invalid_responses, key=lambda item: item[0].stat().st_mtime_ns)
        raise RuntimeError(f"The newest enrollment response is invalid ({candidate}): {problem}")
    if requests:
        request = max(requests, key=lambda path: path.stat().st_mtime_ns)
        raise RuntimeError(
            f"Only an enrollment request was found ({request}). Run the backup-server "
            "provisioning command first; it creates the response JSON."
        )
    raise RuntimeError(
        f"No valid enrollment response JSON was found in {root}. "
        "Use --response to select one from another directory."
    )
