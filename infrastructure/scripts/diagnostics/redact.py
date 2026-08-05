#!/usr/bin/env python3
"""Stream a conservative, agent-safe redaction of production diagnostics."""
from __future__ import annotations

import ipaddress
import re
import sys

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
IPV6 = re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
QUERY_VALUE = re.compile(r"([?&][A-Za-z0-9_.-]+=)[^&\s\"']+")
SECRET_FIELD = re.compile(
    r"(?i)\b(authorization|cookie|set-cookie|api[_-]?key|access[_-]?token|refresh[_-]?token|session)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")


def redact_ipv6(match: re.Match[str]) -> str:
    try:
        address = ipaddress.ip_address(match.group(0))
    except ValueError:
        return match.group(0)
    return "<redacted-ip>" if address.version == 6 else match.group(0)


def redact(line: str) -> str:
    value = ANSI.sub("", line.replace("\x00", ""))
    value = BEARER.sub("Bearer <redacted>", value)
    value = SECRET_FIELD.sub(lambda match: f"{match.group(1)}{match.group(2)}<redacted>", value)
    value = QUERY_VALUE.sub(lambda match: f"{match.group(1)}<redacted>", value)
    value = EMAIL.sub("<redacted-email>", value)
    value = IPV4.sub("<redacted-ip>", value)
    value = IPV6.sub(redact_ipv6, value)
    return value


def main() -> None:
    sys.stdout.write("redaction=ip,email,query-values,credentials,ansi\n")
    for raw in sys.stdin:
        sys.stdout.write(redact(raw))


if __name__ == "__main__":
    main()
