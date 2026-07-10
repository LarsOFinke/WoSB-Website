from __future__ import annotations

from fastapi import status

from app.core.app_error import AppError


class NotFoundAppError(AppError):
    code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND
