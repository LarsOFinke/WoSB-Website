from __future__ import annotations

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 200


class PasswordPolicyError(ValueError):
    pass


def validate_password(password: str) -> None:
    """Validate the deliberately small v1 password policy.

    Length is the only composition rule. This permits password managers and long
    passphrases without imposing brittle character-class requirements.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must contain at least {MIN_PASSWORD_LENGTH} characters."
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must contain at most {MAX_PASSWORD_LENGTH} characters."
        )
