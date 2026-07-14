from __future__ import annotations

import logging
import time
from ipaddress import ip_address
from uuid import uuid4

from app.core.config import settings
from app.core.time import utc_now

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("app.request")

ROUTINE_HEALTH_PATHS = {"/api/health", "/api/health/ready"}


def should_log_request(path: str, status_code: int, failure: Exception | None = None) -> bool:
    """Keep actionable failures while suppressing successful routine probes."""

    return failure is not None or status_code >= 400 or path not in ROUTINE_HEALTH_PATHS


def client_ip_from_request(request: Request) -> str | None:
    peer = request.client.host if request.client else None
    trust_proxy_headers = False
    if peer:
        try:
            parsed_peer = ip_address(peer)
            trust_proxy_headers = parsed_peer.is_private or parsed_peer.is_loopback or parsed_peer.is_link_local
        except ValueError:
            # Starlette's TestClient uses a symbolic peer name. Treat it like a
            # local test proxy while real production peers remain IP-validated.
            trust_proxy_headers = True

    if trust_proxy_headers:
        # Nginx overwrites X-Real-IP with the direct remote address. Prefer it
        # over X-Forwarded-For so a client-supplied left-most value cannot
        # bypass the blocklist or poison security monitoring. For routes
        # without X-Real-IP, the right-most forwarded address is the immediate
        # proxy/client hop appended by Nginx.
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip() or None
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.rsplit(",", 1)[-1].strip() or None
    return peer


def _request_log_context(request: Request, request_id: str, status_code: int, duration_ms: float) -> dict[str, object | None]:
    return {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "client": request.client.host if request.client else None,
        "client_ip": client_ip_from_request(request),
        "forwarded_for": request.headers.get("x-forwarded-for"),
        "user_agent": request.headers.get("user-agent"),
        "query_string": request.url.query or None,
    }


class IpBlockMiddleware(BaseHTTPMiddleware):
    """Reject requests from exact IP addresses managed in the staff panel."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if request.url.path in ROUTINE_HEALTH_PATHS:
            return await call_next(request)

        client_ip = client_ip_from_request(request)
        if not client_ip:
            return await call_next(request)

        block = None
        try:
            from app.db.session import SessionLocal
            from app.modules.admin.services.ip_block_service import find_active_ip_block

            with SessionLocal() as db:
                block = find_active_ip_block(db, client_ip)
        except Exception:
            # Production fails closed so a database outage cannot become an IP
            # block bypass. Development remains fail-open to keep local schema
            # setup and migration troubleshooting possible.
            logger.exception("ip block middleware lookup failed", extra={"client_ip": client_ip})
            if settings.is_production:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "Access-control storage is temporarily unavailable.",
                        "code": "ip_block_store_unavailable",
                    },
                )

        if block is None:
            return await call_next(request)

        payload = {
            "detail": "Access denied for this network address.",
            "code": "ip_blocked",
            "ip_address": block.ip_address,
            "expires_at": block.expires_at.isoformat() if block.expires_at else None,
        }
        headers = {"X-RBF-IP-Blocked": "1"}
        if block.expires_at is not None:
            retry_after = max(1, int((block.expires_at - utc_now()).total_seconds()))
            headers["Retry-After"] = str(retry_after)
        return JSONResponse(status_code=403, content=payload, headers=headers)


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
