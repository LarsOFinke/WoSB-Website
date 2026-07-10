from __future__ import annotations

from fastapi import status

from app.core.app_error import AppError


class ValidationAppError(AppError):
    code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST
