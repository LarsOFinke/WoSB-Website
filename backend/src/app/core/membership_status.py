from __future__ import annotations

from enum import StrEnum


class MembershipStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
