from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260_000


@dataclass(frozen=True)
class PasswordHash:
    algorithm: str
    iterations: int
    salt: bytes
    digest: bytes


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def _parse_password_hash(encoded: str) -> PasswordHash | None:
    try:
        algorithm, iterations, salt, digest = encoded.split("$", 3)
        return PasswordHash(
            algorithm=algorithm,
            iterations=int(iterations),
            salt=_b64decode(salt),
            digest=_b64decode(digest),
        )
    except (ValueError, TypeError):
        return None


def verify_password(password: str, encoded_hash: str) -> bool:
    parsed = _parse_password_hash(encoded_hash)
    if parsed is None or parsed.algorithm != PASSWORD_ALGORITHM:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), parsed.salt, parsed.iterations)
    return hmac.compare_digest(candidate, parsed.digest)


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
