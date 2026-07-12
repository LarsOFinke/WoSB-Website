from __future__ import annotations

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")

ROUTINE_HEALTH_PATHS = {"/api/health", "/api/health/ready"}


def should_log_request(path: str, status_code: int, failure: Exception | None = None) -> bool:
    """Keep actionable failures while suppressing successful routine probes."""

    return failure is not None or status_code >= 400 or path not in ROUTINE_HEALTH_PATHS


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or None
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip() or None
    return request.client.host if request.client else None


def _request_log_context(request: Request, request_id: str, status_code: int, duration_ms: float) -> dict[str, object | None]:
    return {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "client": request.client.host if request.client else None,
        "client_ip": _client_ip(request),
        "forwarded_for": request.headers.get("x-forwarded-for"),
        "user_agent": request.headers.get("user-agent"),
        "query_string": request.url.query or None,
    }


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Add request IDs and persist actionable request/exception logs."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = request.headers.get("x-request-id") or uuid4().hex
        started = time.perf_counter()
        response: Response | None = None
        failure: Exception | None = None
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            failure = exc
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            context = _request_log_context(request, request_id, status_code, duration_ms)
            if failure is not None:
                logger.error(
                    "request failed",
                    extra=context,
                    exc_info=(type(failure), failure, failure.__traceback__),
                )
            elif should_log_request(request.url.path, status_code):
                # Readiness/liveness probes are intentionally excluded from the
                # persisted system log. Failed checks remain visible.
                logger.info("request completed", extra=context)
