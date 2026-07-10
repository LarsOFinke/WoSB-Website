from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.app_error import AppError
from app.core.not_found_app_error import NotFoundAppError
from app.core.permission_app_error import PermissionAppError
from app.core.validation_app_error import ValidationAppError


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": "http_error"},
        headers=exc.headers,
    )


__all__ = [
    "AppError",
    "ValidationAppError",
    "PermissionAppError",
    "NotFoundAppError",
    "app_error_handler",
    "http_error_handler",
]
