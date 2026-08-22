from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
from typing import Any

REQUEST_KIND = "rbf-backup-enrollment-request"
RESPONSE_KIND = "rbf-backup-enrollment-response"
SCHEMA_VERSION = 1

_HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_REMOTE_RE = re.compile(r"^/[A-Za-z0-9._/-]+$")
_ENROLLMENT_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}$")
_SSH_PUBLIC_KEY_RE = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]{1,128})?$"
)
_HOST_KEY_RE = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$"
)
_FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{40,64}$")
_AGE_RECIPIENT_RE = re.compile(r"^age1[0-9a-z]{20,}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _object(payload: object, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return payload


def _text(payload: dict[str, Any], key: str, pattern: re.Pattern[str], label: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not pattern.fullmatch(value):
        raise ValueError(f"Invalid {label}.")
    return value


def _remote_directory(payload: dict[str, Any]) -> str:
    value = _text(payload, "remote_directory", _REMOTE_RE, "remote directory").rstrip("/") or "/"
    if any(part in {"", ".", ".."} for part in value.split("/")[1:]):
        raise ValueError("Invalid remote directory path segments.")
    return value


def validate_request(payload: object) -> dict[str, Any]:
    source = _object(payload, "Enrollment request")
    if source.get("schema_version") != SCHEMA_VERSION or source.get("kind") != REQUEST_KIND:
        raise ValueError("Unsupported enrollment request schema.")
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": REQUEST_KIND,
        "enrollment_id": _text(source, "enrollment_id", _ENROLLMENT_RE, "enrollment id"),
        "ssh_public_key": _text(source, "ssh_public_key", _SSH_PUBLIC_KEY_RE, "SSH public key"),
        "requested_username": _text(source, "requested_username", _USER_RE, "requested username"),
        "requested_directory": _remote_directory({"remote_directory": source.get("requested_directory")}),
        "created_at": str(source.get("created_at") or "").strip(),
        "product_hostname": str(source.get("product_hostname") or "").strip()[:253],
        "release_version": str(source.get("release_version") or "").strip()[:32],
        "provisioner_base64": str(source.get("provisioner_base64") or "").strip(),
        "provisioner_sha256": _text(
            source, "provisioner_sha256", _SHA256_RE, "provisioner checksum"
        ),
        "ingest_script_base64": str(source.get("ingest_script_base64") or "").strip(),
        "ingest_script_sha256": _text(
            source, "ingest_script_sha256", _SHA256_RE, "ingest script checksum"
        ),
    }
    if result["release_version"] and not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+", result["release_version"]
    ):
        raise ValueError("Invalid release version.")
    try:
        provisioner = base64.b64decode(result["provisioner_base64"], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid embedded provisioner.") from exc
    if not provisioner or len(provisioner) > 256 * 1024:
        raise ValueError("Invalid embedded provisioner size.")
    actual_sha256 = hashlib.sha256(provisioner).hexdigest()
    if not hmac.compare_digest(actual_sha256, result["provisioner_sha256"]):
        raise ValueError("Embedded provisioner checksum mismatch.")
    try:
        ingest_script = base64.b64decode(result["ingest_script_base64"], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid embedded ingest script.") from exc
    if not ingest_script or len(ingest_script) > 256 * 1024:
        raise ValueError("Invalid embedded ingest script size.")
    ingest_sha256 = hashlib.sha256(ingest_script).hexdigest()
    if not hmac.compare_digest(ingest_sha256, result["ingest_script_sha256"]):
        raise ValueError("Embedded ingest script checksum mismatch.")
    return result


def validate_response(payload: object, *, expected_enrollment_id: str | None = None) -> dict[str, Any]:
    source = _object(payload, "Enrollment response")
    if source.get("schema_version") != SCHEMA_VERSION or source.get("kind") != RESPONSE_KIND:
        raise ValueError("Unsupported enrollment response schema.")
    enrollment_id = _text(source, "enrollment_id", _ENROLLMENT_RE, "enrollment id")
    if expected_enrollment_id and enrollment_id != expected_enrollment_id:
        raise ValueError("Enrollment response does not match the active request.")
    try:
        port = int(source.get("port") or 22)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid SSH port.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("Invalid SSH port.")
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": RESPONSE_KIND,
        "enrollment_id": enrollment_id,
        "created_at": str(source.get("created_at") or "").strip(),
        "host": _text(source, "host", _HOST_RE, "backup host"),
        "port": port,
        "username": _text(source, "username", _USER_RE, "SSH username"),
        "remote_directory": _remote_directory(source),
        "receipt_directory": _remote_directory(
            {"remote_directory": source.get("receipt_directory")}
        ),
        "recovery_directory": _remote_directory(
            {"remote_directory": source.get("recovery_directory")}
        ),
        "host_key": _text(source, "host_key", _HOST_KEY_RE, "SSH host key"),
        "host_key_fingerprint": _text(
            source, "host_key_fingerprint", _FINGERPRINT_RE, "SSH host-key fingerprint"
        ),
        "age_recipient": _text(source, "age_recipient", _AGE_RECIPIENT_RE, "age recipient"),
        "managed_server": source.get("managed_server") is True,
        "trust_model": str(source.get("trust_model") or "").strip(),
    }
    if result["managed_server"] and result["trust_model"] != "server-controlled-ingest-v1":
        raise ValueError("Managed backup server has an unsupported trust model.")
    return result


def parse_json_document(value: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON.") from exc
    return _object(payload, label)


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
