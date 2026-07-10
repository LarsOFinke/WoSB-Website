from __future__ import annotations


class ConfigError(RuntimeError):
    """Raised when required deployment configuration is missing or invalid."""
