from __future__ import annotations

from dataclasses import dataclass

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 200


class PasswordPolicyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PasswordPolicy:
    minimum_length: int = MIN_PASSWORD_LENGTH
    maximum_length: int = MAX_PASSWORD_LENGTH

    def validate(self, password: str) -> None:
        """Validate a small passphrase-friendly policy without composition rules."""
        if len(password) < self.minimum_length:
            raise PasswordPolicyError(
                f"Password must contain at least {self.minimum_length} characters."
            )
        if len(password) > self.maximum_length:
            raise PasswordPolicyError(
                f"Password must contain at most {self.maximum_length} characters."
            )


_default_policy = PasswordPolicy()


def validate_password(password: str) -> None:
    _default_policy.validate(password)


__all__ = [
    "MAX_PASSWORD_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "PasswordPolicy",
    "PasswordPolicyError",
    "validate_password",
]
