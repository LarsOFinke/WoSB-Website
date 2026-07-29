from __future__ import annotations

import logging
import time
from ipaddress import ip_address
from urllib.parse import urlsplit
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.time import utc_now
from app.modules.admin.models.security_event import (
    SECURITY_SIGNAL_LOGIN_FAILURE,
    SECURITY_SIGNAL_RATE_LIMIT,
    SECURITY_SIGNAL_RECONNAISSANCE,
)

logger = logging.getLogger("app.request")
security_logger = logging.getLogger("app.security")

ROUTINE_HEALTH_PATHS = {"/api/health", "/api/health/ready"}
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
SUSPICIOUS_PATH_PARTS = (
    "/.env",
    "/.git",
    "/wp-admin",
    "/wp-login",
    "/vendor/phpunit",
    "/phpunit",
    "/cgi-bin",
    "/adminer",
    "/server-status",
    "/etc/passwd",
    "/actuator",
    ".php",
)


def _normalized_ip(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate or "," in candidate:
        return None
    try:
        return str(ip_address(candidate))
    except ValueError:
        return None



def _origin_from_referer(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


class SecuritySignalClassifier:
    """Map a completed request to a coarse signal useful for an IP-ban decision.

    Routes are inspected only in memory. The returned signal contains no URL,
    account identifier, user agent or request payload.
    """

    @staticmethod
    def classify(path: str, status_code: int) -> str | None:
        normalized_path = (path or "").casefold()
        if status_code == 429:
            return SECURITY_SIGNAL_RATE_LIMIT
        if normalized_path == "/api/auth/login" and status_code in {400, 401, 403}:
            return SECURITY_SIGNAL_LOGIN_FAILURE
        if status_code >= 400 and any(part in normalized_path for part in SUSPICIOUS_PATH_PARTS):
            return SECURITY_SIGNAL_RECONNAISSANCE
        return None


class RequestLogPolicy:
    def __init__(self, classifier: SecuritySignalClassifier | None = None) -> None:
        self._classifier = classifier or SecuritySignalClassifier()

    def signal_for(self, path: str, status_code: int) -> str | None:
        return self._classifier.classify(path, status_code)

    def should_log(
        self, path: str, status_code: int, failure: Exception | None = None
    ) -> bool:
        # Application failures are operational console events, not grounds for
        # retaining a visitor IP in the ban-candidate store.
        return failure is None and self.signal_for(path, status_code) is not None


class ClientIpResolver:
    def resolve(self, request: Request) -> str | None:
        peer = request.client.host if request.client else None
        if not self._trust_proxy_headers(peer):
            return _normalized_ip(peer)
        real_ip = _normalized_ip(request.headers.get("x-real-ip"))
        if real_ip:
            return real_ip
        forwarded_for = _normalized_ip(request.headers.get("x-forwarded-for"))
        if forwarded_for:
            return forwarded_for
        return _normalized_ip(peer)

    @staticmethod
    def _trust_proxy_headers(peer: str | None) -> bool:
        if not peer:
            return False
        try:
            parsed_peer = ip_address(peer)
            return parsed_peer.is_private or parsed_peer.is_loopback or parsed_peer.is_link_local
        except ValueError:
            # Starlette TestClient uses a symbolic local peer.
            return True


class RequestLogContextFactory:
    """Build non-personal operational context for console errors."""

    def create(
        self,
        request: Request,
        request_id: str,
        status_code: int,
        duration_ms: float,
    ) -> dict[str, object | None]:
        return {
            "request_id": request_id,
            "method": request.method,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }


_request_log_policy = RequestLogPolicy()
_client_ip_resolver = ClientIpResolver()
_request_contexts = RequestLogContextFactory()


def should_log_request(
    path: str, status_code: int, failure: Exception | None = None
) -> bool:
    return _request_log_policy.should_log(path, status_code, failure)


def security_signal_for_request(path: str, status_code: int) -> str | None:
    return _request_log_policy.signal_for(path, status_code)


def client_ip_from_request(request: Request) -> str | None:
    return _client_ip_resolver.resolve(request)


def _request_log_context(
    request: Request, request_id: str, status_code: int, duration_ms: float
) -> dict[str, object | None]:
    return _request_contexts.create(request, request_id, status_code, duration_ms)


class CsrfOriginMiddleware(BaseHTTPMiddleware):
    """Reject cross-origin state changes authenticated by the session cookie."""

    def __init__(self, app, allowed_origins: tuple[str, ...]) -> None:
        super().__init__(app)
        self._allowed_origins = frozenset(origin.rstrip("/") for origin in allowed_origins)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if request.method.upper() in SAFE_METHODS:
            return await call_next(request)
        if not request.cookies.get(settings.session_cookie_name):
            return await call_next(request)

        origin = request.headers.get("origin")
        candidate = origin.rstrip("/") if origin else _origin_from_referer(request.headers.get("referer"))
        if candidate is not None and candidate not in self._allowed_origins:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Cross-origin state-changing request was rejected.",
                    "code": "csrf_origin_rejected",
                },
            )
        if request.headers.get("sec-fetch-site", "").casefold() == "cross-site":
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Cross-site state-changing request was rejected.",
                    "code": "csrf_origin_rejected",
                },
            )
        return await call_next(request)


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
            # Do not copy the client IP into console/container logs.
            logger.exception("ip block middleware lookup failed")
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
            "expires_at": block.expires_at.isoformat() if block.expires_at else None,
        }
        headers = {"X-RBF-IP-Blocked": "1"}
        if block.expires_at is not None:
            retry_after = max(1, int((block.expires_at - utc_now()).total_seconds()))
            headers["Retry-After"] = str(retry_after)
        return JSONResponse(status_code=403, content=payload, headers=headers)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit operational errors and minimal, purpose-bound IP-ban signals."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = uuid4().hex
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

            if failure is not None:
                # The request boundary intentionally avoids exception text and
                # tracebacks: framework errors may contain submitted values.
                logger.error(
                    "request failed",
                    extra=_request_log_context(request, request_id, status_code, duration_ms),
                )
            else:
                signal = security_signal_for_request(request.url.path, status_code)
                client_ip = client_ip_from_request(request) if signal else None
                if signal and client_ip:
                    security_logger.warning(
                        "security event",
                        extra={"security_signal": signal, "client_ip": client_ip},
                    )
