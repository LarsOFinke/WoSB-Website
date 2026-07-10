from __future__ import annotations

from fastapi import status

from app.core.app_error import AppError


class PermissionAppError(AppError):
    code = "permission_denied"
    status_code = status.HTTP_403_FORBIDDEN
