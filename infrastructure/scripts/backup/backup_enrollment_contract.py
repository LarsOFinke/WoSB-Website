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
PULL_TRANSPORT = "recovery-controller-pull-v1"
PULL_TRUST_MODEL = "backup-controller-pull-v1"

_HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_REMOTE_RE = re.compile(r"^/[A-Za-z0-9._/-]+$")
_ENROLLMENT_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}$")
_SSH_PUBLIC_KEY_RE = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) "
    r"[A-Za-z0-9+/=]+(?: [^\r\n]{1,128})?$"
)
_HOST_KEY_RE = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$"
)
_FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{40,64}$")
_AGE_RECIPIENT_RE = re.compile(r"^age1[0-9a-z]{20,}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_ENVIRONMENTS = {"test", "production"}


def _controller_identity(environment: str) -> tuple[str, str]:
    return f"rbf-backup-controller-{environment}", f"/backups/wosb/{environment}"


def _object(payload: object, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return payload


def _text(payload: dict[str, Any], key: str, pattern: re.Pattern[str], label: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not pattern.fullmatch(value):
        raise ValueError(f"Invalid {label}.")
    return value


def _remote(value: object, label: str) -> str:
    path = str(value or "").strip().rstrip("/") or "/"
    if not _REMOTE_RE.fullmatch(path) or any(
        part in {"", ".", ".."} for part in path.split("/")[1:]
    ):
        raise ValueError(f"Invalid {label}.")
    return path


def _embedded(
    source: dict[str, Any], value_key: str, digest_key: str, label: str, limit: int
) -> tuple[str, str]:
    encoded = str(source.get(value_key) or "").strip()
    digest = _text(source, digest_key, _SHA256_RE, f"{label} checksum")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"Invalid embedded {label}.") from exc
    if not content or len(content) > limit:
        raise ValueError(f"Invalid embedded {label} size.")
    if not hmac.compare_digest(hashlib.sha256(content).hexdigest(), digest):
        raise ValueError(f"Embedded {label} checksum mismatch.")
    return encoded, digest


def validate_request(payload: object) -> dict[str, Any]:
    source = _object(payload, "Enrollment request")
    if source.get("schema_version") != SCHEMA_VERSION or source.get("kind") != REQUEST_KIND:
        raise ValueError("Unsupported enrollment request schema.")
    environment = str(source.get("deployment_environment") or "").strip().lower()
    if environment not in _ENVIRONMENTS:
        raise ValueError("Invalid deployment environment.")
    provisioner, provisioner_sha = _embedded(
        source, "provisioner_base64", "provisioner_sha256", "provisioner", 256 * 1024
    )
    recovery_tool, recovery_tool_sha = _embedded(
        source,
        "recovery_tool_base64",
        "recovery_tool_sha256",
        "Recovery Tool",
        1024 * 1024,
    )
    try:
        website_port = int(source.get("website_ssh_port") or 22)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid website SSH port.") from exc
    if not 1 <= website_port <= 65535:
        raise ValueError("Invalid website SSH port.")
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": REQUEST_KIND,
        "enrollment_id": _text(source, "enrollment_id", _ENROLLMENT_RE, "enrollment id"),
        "deployment_environment": environment,
        "created_at": str(source.get("created_at") or "").strip(),
        "product_hostname": str(source.get("product_hostname") or "").strip()[:253],
        "release_version": str(source.get("release_version") or "").strip()[:32],
        "website_host": _text(source, "website_host", _HOST_RE, "website SSH host"),
        "website_ssh_port": website_port,
        "website_host_key": _text(
            source, "website_host_key", _HOST_KEY_RE, "website SSH host key"
        ),
        "website_host_key_fingerprint": _text(
            source,
            "website_host_key_fingerprint",
            _FINGERPRINT_RE,
            "website SSH host-key fingerprint",
        ),
        "requested_controller_username": _text(
            source, "requested_controller_username", _USER_RE, "controller username"
        ),
        "requested_storage_directory": _remote(
            source.get("requested_storage_directory"), "controller storage directory"
        ),
        "provisioner_base64": provisioner,
        "provisioner_sha256": provisioner_sha,
        "recovery_tool_base64": recovery_tool,
        "recovery_tool_sha256": recovery_tool_sha,
    }
    if (
        result["requested_controller_username"],
        result["requested_storage_directory"],
    ) != _controller_identity(environment):
        raise ValueError("Enrollment request identity does not match its deployment environment.")
    if result["release_version"] and not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+", result["release_version"]
    ):
        raise ValueError("Invalid release version.")
    return result


def validate_response(
    payload: object,
    *,
    expected_enrollment_id: str | None = None,
    expected_environment: str | None = None,
) -> dict[str, Any]:
    source = _object(payload, "Enrollment response")
    if source.get("schema_version") != SCHEMA_VERSION or source.get("kind") != RESPONSE_KIND:
        raise ValueError("Unsupported enrollment response schema.")
    enrollment_id = _text(source, "enrollment_id", _ENROLLMENT_RE, "enrollment id")
    if expected_enrollment_id and enrollment_id != expected_enrollment_id:
        raise ValueError("Enrollment response does not match the active request.")
    environment = str(source.get("deployment_environment") or "").strip().lower()
    if environment not in _ENVIRONMENTS or (
        expected_environment and environment != expected_environment
    ):
        raise ValueError("Enrollment response belongs to a different deployment environment.")
    try:
        port = int(source.get("port") or 22)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid website SSH port.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("Invalid website SSH port.")
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": RESPONSE_KIND,
        "enrollment_id": enrollment_id,
        "deployment_environment": environment,
        "created_at": str(source.get("created_at") or "").strip(),
        "host": _text(source, "host", _HOST_RE, "website host"),
        "port": port,
        "username": _text(source, "username", _USER_RE, "controller username"),
        "storage_directory": _remote(
            source.get("storage_directory"), "controller storage directory"
        ),
        "remote_directory": _remote(source.get("remote_directory"), "export directory"),
        "request_directory": _remote(source.get("request_directory"), "request directory"),
        "status_directory": _remote(source.get("status_directory"), "status directory"),
        "acknowledgement_directory": _remote(
            source.get("acknowledgement_directory"), "acknowledgement directory"
        ),
        "host_key": _text(source, "host_key", _HOST_KEY_RE, "website SSH host key"),
        "host_key_fingerprint": _text(
            source, "host_key_fingerprint", _FINGERPRINT_RE, "website host-key fingerprint"
        ),
        "age_recipient": _text(source, "age_recipient", _AGE_RECIPIENT_RE, "age recipient"),
        "controller_public_key": _text(
            source, "controller_public_key", _SSH_PUBLIC_KEY_RE, "controller public key"
        ),
        "managed_server": source.get("managed_server") is True,
        "trust_model": str(source.get("trust_model") or "").strip(),
        "transport": str(source.get("transport") or "").strip(),
    }
    if (result["username"], result["storage_directory"]) != _controller_identity(environment):
        raise ValueError("Enrollment response identity does not match its deployment environment.")
    if (
        not result["managed_server"]
        or result["trust_model"] != PULL_TRUST_MODEL
        or result["transport"] != PULL_TRANSPORT
        or result["remote_directory"] != "/exports"
        or result["request_directory"] != "/requests"
        or result["status_directory"] != "/status"
        or result["acknowledgement_directory"] != "/acknowledgements"
    ):
        raise ValueError("Managed backup controller has an unsupported trust boundary.")
    return result


def parse_json_document(value: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON.") from exc
    return _object(payload, label)


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
