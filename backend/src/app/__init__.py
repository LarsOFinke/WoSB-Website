"""Royal Blackwater Vanguards backend package."""

from typing import Any


def create_app() -> Any:
    """Import the application factory lazily to keep tooling side effects minimal."""
    from app.core.app_factory import create_app as factory

    return factory()


__all__ = ["create_app"]
