#!/usr/bin/env python3
"""Fail closed when mutating API operations fall outside the reviewed security policy."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OPENAPI = ROOT / "openapi/openapi.json"
SECURITY = ROOT / "spring-api/src/main/java/eu/royalblackwater/api/config/SecurityConfiguration.java"
MUTATING_METHODS = ("post", "put", "patch", "delete")

# Anonymous mutations are protected by validation, rate limiting and the request
# boundary. Keep this list aligned with the method-specific permitAll matchers.
PUBLIC_MUTATIONS = {
    ("post", "/api/auth/login"),
    ("post", "/api/auth/logout"),
    ("post", "/api/auth/register"),
    ("post", "/api/privacy/contact"),
    ("post", "/api/privacy/cookie-consent"),
}

# These authenticated mutations intentionally remain available to ordinary
# accounts. Every other non-admin mutation must match a staff endpoint catalog.
AUTHENTICATED_SELF_SERVICE = {
    ("post", "/api/auth/change-password"),
    ("post", "/api/fleets/join"),
    ("post", "/api/groups/{group_id}/join"),
    ("post", "/api/privacy/requests"),
    ("put", "/api/profile"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[authorization-policy] {message}")


def java_array(source: str, name: str) -> tuple[str, ...]:
    match = re.search(rf"\b{name}\s*=\s*\{{(.*?)\}};", source, re.S)
    require(match is not None, f"missing SecurityConfiguration catalog {name}")
    return tuple(re.findall(r'"([^"]+)"', match.group(1)))


def ant_matches(pattern: str, path: str) -> bool:
    expression = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]+")
    return re.fullmatch(expression, path) is not None


def main() -> None:
    document = json.loads(OPENAPI.read_text(encoding="utf-8"))
    security = SECURITY.read_text(encoding="utf-8")
    staff_patterns = {
        method: java_array(security, f"STAFF_{method.upper()}_ENDPOINTS")
        for method in ("post", "put", "delete")
    }
    operations = {
        (method, path)
        for path, item in document["paths"].items()
        for method in MUTATING_METHODS
        if method in item
    }

    reviewed_exceptions = PUBLIC_MUTATIONS | AUTHENTICATED_SELF_SERVICE
    require(reviewed_exceptions <= operations,
            f"reviewed exceptions no longer exist in OpenAPI: {sorted(reviewed_exceptions - operations)}")

    for method, patterns in staff_patterns.items():
        require(len(patterns) == len(set(patterns)), f"duplicate {method.upper()} staff endpoint pattern")
        method_paths = {path for operation_method, path in operations if operation_method == method}
        for pattern in patterns:
            matches = {path for path in method_paths if ant_matches(pattern, path)}
            require(matches, f"{method.upper()} staff pattern matches no OpenAPI operation: {pattern}")
            require(not matches & {path for _, path in reviewed_exceptions},
                    f"{method.upper()} staff pattern also matches a reviewed exception: {pattern}")

    classifications: dict[tuple[str, str], str] = {}
    for operation in sorted(operations):
        method, path = operation
        if operation in PUBLIC_MUTATIONS:
            classifications[operation] = "public"
        elif path.startswith("/api/admin/"):
            classifications[operation] = "admin"
        elif method in staff_patterns and any(ant_matches(pattern, path) for pattern in staff_patterns[method]):
            classifications[operation] = "staff"
        elif operation in AUTHENTICATED_SELF_SERVICE:
            classifications[operation] = "self-service"
        else:
            require(False, f"unclassified mutating OpenAPI operation: {method.upper()} {path}")

    counts = {category: tuple(classifications.values()).count(category)
              for category in ("public", "self-service", "staff", "admin")}
    print("[authorization-policy] OK: " + ", ".join(f"{name}={count}" for name, count in counts.items()))


if __name__ == "__main__":
    main()
