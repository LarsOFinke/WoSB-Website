from __future__ import annotations

from enum import StrEnum


class DatabaseSchemaMode(StrEnum):
    """Controls who owns schema creation for a deployment."""

    CREATE = "create"
    MIGRATE = "migrate"
    NONE = "none"
