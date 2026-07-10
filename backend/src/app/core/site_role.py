from __future__ import annotations

from enum import StrEnum


class SiteRole(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
