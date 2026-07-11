from __future__ import annotations

import pytest

from app.core.password_policy import MIN_PASSWORD_LENGTH, PasswordPolicyError, validate_password


def test_password_policy_accepts_long_passphrases_without_composition_rules() -> None:
    validate_password("correct horse battery staple")


def test_password_policy_rejects_short_passwords() -> None:
    with pytest.raises(PasswordPolicyError, match=str(MIN_PASSWORD_LENGTH)):
        validate_password("too-short")
