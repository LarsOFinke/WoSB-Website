from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.configuration.models import Settings
from app.core.config import settings


class SecretBoxError(ValueError):
    """Raised when an encrypted application secret cannot be decoded safely."""


@dataclass(frozen=True, slots=True)
class SecretBox:
    """Versioned authenticated encryption with explicit key rotation.

    The first configured Fernet key encrypts new values. All configured keys can
    decrypt older values. A deployment-derived compatibility key remains last so
    installations created before WEBHOOK_ENCRYPTION_KEYS can upgrade safely.
    """

    primary: Fernet
    cryptor: MultiFernet
    prefix: str = "fernet:v1:"

    @classmethod
    def for_webhooks(cls, application_settings: Settings) -> "SecretBox":
        configured = list(application_settings.webhook_encryption_keys)
        derived = cls._derived_key(application_settings.database_url)
        keys = [*configured]
        if derived not in keys:
            keys.append(derived)
        fernets = [Fernet(key.encode("ascii")) for key in keys]
        return cls(primary=fernets[0], cryptor=MultiFernet(fernets))

    @staticmethod
    def _derived_key(database_url: str) -> str:
        material = f"royal-blackwater-fleet:webhooks:v1:{database_url}".encode("utf-8")
        return base64.urlsafe_b64encode(hashlib.sha256(material).digest()).decode("ascii")

    def is_encrypted(self, value: str | None) -> bool:
        return bool(value and value.startswith(self.prefix))

    def encrypt(self, value: str) -> str:
        if self.is_encrypted(value):
            return value
        token = self.primary.encrypt(value.encode("utf-8")).decode("ascii")
        return f"{self.prefix}{token}"

    def decrypt(self, value: str) -> str:
        if not self.is_encrypted(value):
            return value
        token = value[len(self.prefix) :]
        try:
            return self.cryptor.decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, UnicodeEncodeError) as exc:
            raise SecretBoxError("Stored webhook credential could not be decrypted.") from exc

    def needs_rotation(self, value: str) -> bool:
        """Return whether ciphertext is valid but not encrypted by the primary key."""
        if not self.is_encrypted(value):
            return True
        token = value[len(self.prefix) :].encode("ascii")
        try:
            self.primary.decrypt(token)
            return False
        except InvalidToken:
            try:
                self.cryptor.decrypt(token)
            except InvalidToken as exc:
                raise SecretBoxError("Stored webhook credential could not be decrypted.") from exc
            return True

    def rotate(self, value: str) -> str:
        if not self.is_encrypted(value):
            return self.encrypt(value)
        if not self.needs_rotation(value):
            return value
        token = value[len(self.prefix) :].encode("ascii")
        try:
            rotated = self.cryptor.rotate(token).decode("ascii")
        except InvalidToken as exc:
            raise SecretBoxError("Stored webhook credential could not be decrypted.") from exc
        return f"{self.prefix}{rotated}"


webhook_secret_box = SecretBox.for_webhooks(settings)


__all__ = ["SecretBox", "SecretBoxError", "webhook_secret_box"]
