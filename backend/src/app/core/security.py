from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000


@dataclass(frozen=True, slots=True)
class PasswordHash:
    algorithm: str
    iterations: int
    salt: bytes
    digest: bytes


class PasswordHasher:
    def __init__(
        self,
        *,
        algorithm: str = PASSWORD_ALGORITHM,
        iterations: int = PASSWORD_ITERATIONS,
    ) -> None:
        self.algorithm = algorithm
        self.iterations = iterations

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.iterations
        )
        return (
            f"{self.algorithm}${self.iterations}$"
            f"{self._b64encode(salt)}${self._b64encode(digest)}"
        )

    def verify(self, password: str, encoded_hash: str) -> bool:
        parsed = self.parse(encoded_hash)
        if parsed is None or parsed.algorithm != self.algorithm:
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), parsed.salt, parsed.iterations
        )
        return hmac.compare_digest(candidate, parsed.digest)

    def needs_rehash(self, encoded_hash: str) -> bool:
        parsed = self.parse(encoded_hash)
        return (
            parsed is None
            or parsed.algorithm != self.algorithm
            or parsed.iterations < self.iterations
        )

    @classmethod
    def parse(cls, encoded: str) -> PasswordHash | None:
        try:
            algorithm, iterations, salt, digest = encoded.split("$", 3)
            return PasswordHash(
                algorithm=algorithm,
                iterations=int(iterations),
                salt=cls._b64decode(salt),
                digest=cls._b64decode(digest),
            )
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _b64encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

    @staticmethod
    def _b64decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))


class SessionTokenService:
    @staticmethod
    def create() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


_password_hasher = PasswordHasher()
_session_tokens = SessionTokenService()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    return _password_hasher.verify(password, encoded_hash)


def password_hash_needs_rehash(encoded_hash: str) -> bool:
    return _password_hasher.needs_rehash(encoded_hash)


def create_session_token() -> str:
    return _session_tokens.create()


def hash_session_token(token: str) -> str:
    return _session_tokens.hash(token)


__all__ = [
    "PASSWORD_ALGORITHM",
    "PASSWORD_ITERATIONS",
    "PasswordHash",
    "PasswordHasher",
    "SessionTokenService",
    "create_session_token",
    "hash_password",
    "hash_session_token",
    "password_hash_needs_rehash",
    "verify_password",
]
