from __future__ import annotations

from fastapi import status


class AppError(Exception):
    """Base application error with an HTTP mapping."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "app_error"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
