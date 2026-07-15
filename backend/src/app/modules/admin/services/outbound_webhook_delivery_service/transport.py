from __future__ import annotations

import hashlib
import hmac
import http.client
import ipaddress
import socket
import ssl
from collections.abc import Callable, Iterable
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request

from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery


class WebhookTargetError(OSError):
    pass


def _public_target_addresses(
    hostname: str,
    port: int,
    resolver: Callable[..., Iterable[tuple[Any, ...]]] = socket.getaddrinfo,
) -> tuple[str, ...]:
    try:
        records = resolver(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise
    addresses = tuple(dict.fromkeys(str(record[4][0]) for record in records))
    if not addresses:
        raise WebhookTargetError(f"Webhook host '{hostname}' resolved to no usable address.")
    for value in addresses:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise WebhookTargetError(
                f"Webhook host '{hostname}' resolved to an invalid address."
            ) from exc
        if not address.is_global:
            raise WebhookTargetError(
                f"Webhook host '{hostname}' resolves to a non-public address and is blocked."
            )
    return addresses


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, address: str, timeout: int) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._address = address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._address, self.port), self.timeout, self.source_address
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, address: str, timeout: int) -> None:
        super().__init__(
            host,
            port=port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self._address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._address, self.port), self.timeout, self.source_address
        )
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


class WebhookSigner:
    @staticmethod
    def headers(
        row: OutboundWebhookDelivery,
        secret: str,
        timestamp: str,
    ) -> dict[str, str]:
        signed_payload = f"{timestamp}.{row.delivery_id}.{row.payload_json}".encode("utf-8")
        signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "RoyalBlackwaterFleet-Webhook/1.0",
            "X-RBF-Event": row.event_type,
            "X-RBF-Delivery": row.delivery_id,
            "X-RBF-Timestamp": timestamp,
            "X-RBF-Signature": f"sha256={signature}",
            "X-RBF-Signature-Version": "v2",
        }


class WebhookTransport:
    """Send directly to one validated public IP without following redirects.

    DNS is resolved once, every returned address must be globally routable and
    the connection is pinned to the selected address while TLS still validates
    the original hostname. This closes private-target, redirect and DNS-rebinding
    paths that a generic URL opener would leave available.
    """

    def __init__(
        self,
        *,
        resolver: Callable[..., Iterable[tuple[Any, ...]]] = socket.getaddrinfo,
        timeout_seconds: int = 8,
    ) -> None:
        self._resolver = resolver
        self._timeout_seconds = timeout_seconds

    def send(self, request: Request) -> tuple[int, str]:
        parsed = urlsplit(request.full_url)
        hostname = parsed.hostname
        if parsed.scheme not in {"http", "https"} or not hostname:
            raise WebhookTargetError("Webhook target URL is invalid.")
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except ValueError as exc:
            raise WebhookTargetError("Webhook target port is invalid.") from exc

        addresses = _public_target_addresses(hostname, port, self._resolver)
        address = addresses[0]
        connection: http.client.HTTPConnection
        if parsed.scheme == "https":
            connection = _PinnedHTTPSConnection(
                hostname, port, address, self._timeout_seconds
            )
        else:
            connection = _PinnedHTTPConnection(
                hostname, port, address, self._timeout_seconds
            )

        target = parsed.path or "/"
        if parsed.query:
            target = f"{target}?{parsed.query}"
        headers = {key: value for key, value in request.header_items()}
        try:
            connection.request(
                request.get_method(),
                target,
                body=request.data,
                headers=headers,
            )
            response = connection.getresponse()
            body = response.read(4096).decode("utf-8", errors="replace")
            return int(response.status), body
        finally:
            connection.close()

    @staticmethod
    def error_message(endpoint_url: str, exc: Exception) -> str:
        host = urlsplit(endpoint_url).hostname or "configured endpoint"
        reason = exc.reason if isinstance(exc, URLError) else exc
        if isinstance(reason, socket.gaierror):
            return (
                f"DNS resolution failed for webhook host '{host}'. "
                "Verify the API container outbound network and DNS configuration."
            )
        if isinstance(reason, WebhookTargetError):
            return str(reason)[:2000]
        if isinstance(exc, TimeoutError):
            return f"Connection to webhook host '{host}' timed out."
        return str(exc)[:2000]
