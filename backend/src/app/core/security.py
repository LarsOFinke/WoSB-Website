from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.core.config import settings

_HASH_NAME = "sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 16
_TOKEN_PREFIX = "wosb1"


def hash_password(password: str) -> str:
    """Dependency-free password hashing helper for the MVP blueprint.

    Format: pbkdf2_sha256$iterations$salt_hex$digest_hex
    For production, prefer Argon2/passlib plus central auth hardening.
    """

    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_{_HASH_NAME}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
        if algorithm != f"pbkdf2_{_HASH_NAME}":
            return False
        digest = hashlib.pbkdf2_hmac(
            _HASH_NAME,
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(digest.hex(), digest_hex)


def create_access_token(user_id: int) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + settings.access_token_ttl_seconds,
        "nonce": secrets.token_urlsafe(12),
    }
    payload_part = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature_part = _sign(payload_part)
    return f"{_TOKEN_PREFIX}.{payload_part}.{signature_part}"


def verify_access_token(token: str) -> int | None:
    try:
        prefix, payload_part, signature_part = token.split(".", 2)
        if prefix != _TOKEN_PREFIX:
            return None
        expected_signature = _sign(payload_part)
        if not hmac.compare_digest(signature_part, expected_signature):
            return None
        payload = json.loads(_base64url_decode(payload_part))
        return _validate_token_payload(payload)
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _validate_token_payload(payload: dict[str, Any]) -> int | None:
    subject = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(subject, str) or not subject.isdigit():
        return None
    if not isinstance(expires_at, int) or expires_at < int(time.time()):
        return None
    return int(subject)


def _sign(payload_part: str) -> str:
    digest = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        payload_part.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
