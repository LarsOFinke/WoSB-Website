from __future__ import annotations

import hashlib
import hmac
import socket
from collections.abc import Callable
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery


class WebhookSigner:
    @staticmethod
    def headers(
        row: OutboundWebhookDelivery,
        secret: str,
        timestamp: str,
    ) -> dict[str, str]:
        signature = hmac.new(
            secret.encode("utf-8"),
            row.payload_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "RoyalBlackwaterFleet-Webhook/1.0",
            "X-RBF-Event": row.event_type,
            "X-RBF-Delivery": row.delivery_id,
            "X-RBF-Timestamp": timestamp,
            "X-RBF-Signature": f"sha256={signature}",
        }


class WebhookTransport:
    def __init__(self, opener: Callable[..., Any] = urlopen, timeout_seconds: int = 8) -> None:
        self._opener = opener
        self._timeout_seconds = timeout_seconds

    def send(self, request: Request) -> tuple[int, str]:
        with self._opener(request, timeout=self._timeout_seconds) as response:
            body = response.read(4096).decode("utf-8", errors="replace")
            return int(response.status), body

    @staticmethod
    def error_message(endpoint_url: str, exc: Exception) -> str:
        host = urlparse(endpoint_url).hostname or "configured endpoint"
        reason = exc.reason if isinstance(exc, URLError) else exc
        if isinstance(reason, socket.gaierror):
            return (
                f"DNS resolution failed for webhook host '{host}'. "
                "Verify the API container outbound network and DNS configuration."
            )
        if isinstance(exc, TimeoutError):
            return f"Connection to webhook host '{host}' timed out."
        return str(exc)[:2000]
